import unittest
from contextlib import contextmanager
from unittest.mock import Mock
from flask import Flask
from api_v1 import AccessState, Identity, install_api_v1
from v1_assignment_options import AssignmentOptionsService

USER='00000000-0000-4000-8000-000000000001'
SESSION='00000000-0000-4000-8000-000000000002'
STAMP='2026-10-20T00:00:00+00:00'


class AssignmentOptionTests(unittest.TestCase):
    def setUp(self):
        self.result={'code':None,'rows':[]}
        self.calls=[]
        @contextmanager
        def connect():
            cursor=Mock()
            cursor.execute.side_effect=lambda *args:self.calls.append(args)
            cursor.fetchone.side_effect=lambda:{'result':self.result}
            connection=Mock()
            connection.cursor.return_value.__enter__=Mock(return_value=cursor)
            connection.cursor.return_value.__exit__=Mock(return_value=False)
            yield connection
        self.service=AssignmentOptionsService(connect,cursor_key=b'x'*32,now=lambda:1000)
        self.backend=Mock()
        self.backend.authenticate.return_value=Identity(USER,SESSION)
        self.backend.load_access.return_value=AccessState(USER,'Fictional','teacher','active',False,'v1','v1')
        self.backend.assignment_options_service=self.service
        app=Flask(__name__)
        install_api_v1(app,self.backend)
        self.client=app.test_client()
        self.headers={'Authorization':'Bearer fictional'}

    def get(self,path='/schools/1/assignment-options'):
        return self.client.get('/api/v1'+path,headers=self.headers)

    def test_empty_options_have_no_store_and_no_implicit_directory_data(self):
        response=self.get()
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['data'],[])
        self.assertEqual(response.json['page'],{'next_cursor':None})
        self.assertEqual(response.headers['Cache-Control'],'no-store')

    def test_strict_filters_ids_and_role_guard(self):
        for path in ['/schools/01/assignment-options','/schools/1/assignment-options?q=x',
                     '/schools/1/assignment-options?limit=101','/schools/1/assignment-options?limit=1&limit=2']:
            self.assertEqual(self.get(path).status_code,422)
        self.backend.load_access.return_value=AccessState(USER,'Fictional','parent','active',False,'v1','v1')
        self.assertEqual(self.get().status_code,403)
        self.assertEqual(self.calls,[])

    def test_uuid_cursor_preserves_internal_order_metadata_but_hides_it_in_data(self):
        self.result['rows']=[{'data':{'user_id':SESSION,'role':'parent','full_name':'Fictional'},'created_at':STAMP},
                             {'data':{'user_id':USER,'role':'teacher','full_name':'Fictional'},'created_at':STAMP}]
        response=self.get('/schools/1/assignment-options?limit=1')
        token=response.json['page']['next_cursor']
        self.assertNotIn('created_at',response.json['data'][0])
        self.result['rows']=[]
        self.assertEqual(self.get('/schools/1/assignment-options?limit=1&cursor='+token).status_code,200)
        self.assertEqual(self.calls[-1][1][3:5],(STAMP,SESSION))
        self.assertEqual(self.get('/schools/2/assignment-options?limit=1&cursor='+token).status_code,422)

    def test_grade_filter_is_strict_and_bound_into_cursor(self):
        self.result['rows']=[{'data':{'user_id':SESSION,'role':'expert','full_name':'Synthetic','grade_levels':[2]},'created_at':STAMP},
            {'data':{'user_id':USER,'role':'teacher','full_name':'Synthetic','grade_levels':[2]},'created_at':STAMP}]
        response=self.get('/schools/1/assignment-options?limit=1&grade_level=2')
        self.assertEqual(response.status_code,200);self.assertEqual(response.json['data'][0]['grade_levels'],[2])
        self.assertIn('assignment_options_by_grade',self.calls[-1][0]);self.assertEqual(self.calls[-1][1][3],2)
        token=response.json['page']['next_cursor'];self.result['rows']=[]
        self.assertEqual(self.get('/schools/1/assignment-options?limit=1&grade_level=2&cursor='+token).status_code,200)
        self.assertEqual(self.get('/schools/1/assignment-options?limit=1&grade_level=1&cursor='+token).status_code,422)
        for grade in ['0','4','02','', 'true']:
            self.assertEqual(self.get('/schools/1/assignment-options?grade_level='+grade).status_code,422)

    def test_current_sql_denial_overrides_previous_guard_access(self):
        for code,status in [('AUTHENTICATION_REQUIRED',401),('FORBIDDEN',403),
                            ('PRIVACY_ACCEPTANCE_REQUIRED',403),('NOT_FOUND',404)]:
            self.result={'code':code,'rows':[]}
            self.assertEqual(self.get().status_code,status)

    def test_parent_lookup_uses_exact_normalized_email_and_current_school_grade(self):
        self.result['rows']=[{'data':{'user_id':SESSION,'role':'parent','full_name':'Fictional Parent'},'created_at':STAMP}]
        response=self.get('/schools/1/assignment-options?grade_level=2&parent_email=Parent%40Example.invalid')
        self.assertEqual(response.status_code,200)
        self.assertIn('graphiscan_teacher_parent_options',self.calls[-1][0])
        self.assertEqual(self.calls[-1][1],(USER,SESSION,'1',2,'parent@example.invalid'))
        self.assertEqual(response.json['page'],{'next_cursor':None})
        self.assertEqual(set(response.json['data'][0]),{'user_id','role','full_name'})

    def test_parent_lookup_refuses_broad_or_cursor_queries(self):
        for query in ['parent_email=parent%40example.invalid','grade_level=1&parent_email=',
                      'grade_level=1&parent_email=parent','grade_level=1&parent_email=%25',
                      'grade_level=1&parent_email=a%40b.invalid&cursor=anything',
                      'grade_level=1&parent_email=a%40b.invalid&parent_email=c%40d.invalid']:
            self.assertEqual(self.get('/schools/1/assignment-options?'+query).status_code,422)
        self.assertEqual(self.calls,[])

    def test_parent_lookup_does_not_return_a_directory_or_private_fields(self):
        row={'data':{'user_id':SESSION,'role':'parent','full_name':'Fictional'},'created_at':STAMP}
        for rows in [[row,row],[{'data':{**row['data'],'email':'private@example.invalid'}}],
                     [{'data':{**row['data'],'role':'teacher'}}]]:
            self.result={'code':None,'rows':rows}
            response=self.get('/schools/1/assignment-options?grade_level=1&parent_email=parent%40example.invalid')
            self.assertEqual(response.status_code,503)
            self.assertNotIn('private@example.invalid',response.text)

    def test_malformed_or_unknown_result_is_sanitized(self):
        for result in [None,{'code':'private SQL','rows':[]},{'code':None,'rows':None}]:
            self.result=result
            response=self.get()
            self.assertEqual(response.status_code,503)
            self.assertNotIn('private',response.text)
