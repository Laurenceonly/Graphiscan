"""Role assignment API/validation tests; no real accounts or database calls."""
import json
import unittest
from dataclasses import replace
from unittest.mock import Mock

from flask import Flask
from api_v1 import AccessState, ApiError, Grant, Identity, install_api_v1
from v1_role_assignments import RoleAssignmentsService, validate_role_assignments

ACTOR='00000000-0000-4000-8000-000000000001'
SESSION='00000000-0000-4000-8000-000000000002'
TARGET='00000000-0000-4000-8000-000000000003'


class RoleAssignmentsTests(unittest.TestCase):
    def setUp(self):
        self.state=AccessState(ACTOR,'Synthetic Admin','admin','active',False,'v1','v1',grants=(Grant('accounts.manage'),))
        self.reader,self.writer=Mock(),Mock()
        self.data={'user_id':TARGET,'role':'teacher','revision':7,'school_grades':[],'students':[]}
        for repository in [self.reader,self.writer]:
            repository.execute.side_effect=lambda *args:{'result':{'code':None,'data':self.data}}
        self.service=RoleAssignmentsService(self.reader,self.writer)
        backend=Mock();backend.authenticate.return_value=Identity(ACTOR,SESSION);backend.load_access.side_effect=lambda *args:self.state
        backend.role_assignments_service=self.service
        app=Flask(__name__);install_api_v1(app,backend)
        self.client=app.test_client();self.headers={'Authorization':'Bearer synthetic'};self.url='/api/v1/accounts/'+TARGET+'/assignments'

    def test_read_is_no_store_and_target_bound(self):
        response=self.client.get(self.url,headers=self.headers)
        self.assertEqual(response.status_code,200);self.assertEqual(response.json['data'],self.data)
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(self.reader.execute.call_args.args[1],(ACTOR,SESSION,TARGET))
        self.writer.execute.assert_not_called()

    def test_grade_write_retains_identity_and_revision(self):
        body={'expected_revision':7,'school_grades':[{'school_id':'2','grade_level':3}]}
        response=self.client.patch(self.url,json=body,headers=self.headers)
        self.assertEqual(response.status_code,200)
        sql,params=self.writer.execute.call_args.args
        self.assertIn('graphiscan_set_role_assignments',sql);self.assertEqual(params[:3],(ACTOR,SESSION,TARGET))
        self.assertEqual(json.loads(params[3]),body);self.reader.execute.assert_not_called()

    def test_parent_delta_retains_student_revision_and_link_choice(self):
        self.data['role']='parent'
        body={'expected_revision':7,'student_links':[{'student_id':'1','expected_revision':9,'linked':False}]}
        self.assertEqual(self.client.patch(self.url,json=body,headers=self.headers).status_code,200)
        self.assertEqual(json.loads(self.writer.execute.call_args.args[1][3]),body)

    def test_global_permission_and_role_guards(self):
        self.assertEqual(self.client.get(self.url).status_code,401)
        for state in [replace(self.state,role='teacher'),replace(self.state,grants=()),replace(self.state,grants=(Grant('accounts.manage','1'),)),replace(self.state,must_change_password=True)]:
            self.state=state
            self.assertIn(self.client.get(self.url,headers=self.headers).status_code,(401,403))
        self.reader.execute.assert_not_called()

    def test_query_and_media_type_rejected(self):
        self.assertEqual(self.client.get(self.url+'?school_id=1',headers=self.headers).status_code,400)
        self.assertEqual(self.client.patch(self.url,data='text',headers=self.headers).status_code,400)
        self.assertEqual(self.client.patch(self.url+'?x=1',json={},headers=self.headers).status_code,400)
        self.writer.execute.assert_not_called()

    def test_invalid_bodies_do_not_reach_database(self):
        cases=[{}, {'expected_revision':True,'school_grades':[]}, {'expected_revision':7,'actor_id':ACTOR,'school_grades':[]},
            {'expected_revision':7,'school_grades':[],'student_links':[]},
            {'expected_revision':7,'school_grades':[{'school_id':'01','grade_level':1}]},
            {'expected_revision':7,'school_grades':[{'school_id':'1','grade_level':True}]},
            {'expected_revision':7,'school_grades':[{'school_id':'1','grade_level':4}]},
            {'expected_revision':7,'school_grades':[{'school_id':'1','grade_level':1}]*2},
            {'expected_revision':7,'school_grades':[{'school_id':'1','grade_level':1,'actor_id':ACTOR}]},
            {'expected_revision':7,'student_links':[]},
            {'expected_revision':7,'student_links':[{'student_id':'1','expected_revision':1,'linked':'true'}]},
            {'expected_revision':7,'student_links':[{'student_id':'1','expected_revision':False,'linked':True}]},
            {'expected_revision':7,'student_links':[{'student_id':'1','expected_revision':1,'linked':True}]*2}]
        for body in cases:
            with self.subTest(body=body):self.assertEqual(self.client.patch(self.url,json=body,headers=self.headers).status_code,422)
        self.writer.execute.assert_not_called()

    def test_scope_bounds_and_empty_revocation(self):
        self.assertEqual(validate_role_assignments({'expected_revision':1,'school_grades':[]})['school_grades'],[])
        scopes=[{'school_id':str(school),'grade_level':grade} for school in range(1,129) for grade in (1,2,3)]
        self.assertEqual(len(validate_role_assignments({'expected_revision':1,'school_grades':scopes})['school_grades']),384)
        with self.assertRaises(ApiError):validate_role_assignments({'expected_revision':1,'school_grades':scopes+[{'school_id':'129','grade_level':1}]})

    def test_database_denial_is_authoritative(self):
        self.writer.execute.side_effect=None
        for code,status in [('REVISION_CONFLICT',409),('FORBIDDEN',403),('NOT_FOUND',404),('INVALID_INPUT',422),('AUTHENTICATION_REQUIRED',401)]:
            self.writer.execute.return_value={'result':{'code':code}}
            response=self.client.patch(self.url,json={'expected_revision':7,'school_grades':[]},headers=self.headers)
            self.assertEqual(response.status_code,status);self.assertEqual(response.json['error']['code'],code)

    def test_configuration_driver_and_malformed_results_fail_closed(self):
        for repository in [None,Mock()]:
            if repository is not None:repository.execute.side_effect=RuntimeError('private DSN')
            self.service.writer=repository
            response=self.client.patch(self.url,json={'expected_revision':7,'school_grades':[]},headers=self.headers)
            self.assertEqual(response.status_code,503);self.assertNotIn('private DSN',response.text)
        self.reader.execute.side_effect=None;self.reader.execute.return_value={'result':{'code':None,'data':{'user_id':ACTOR}}}
        self.assertEqual(self.client.get(self.url,headers=self.headers).status_code,503)


if __name__=='__main__':unittest.main()
