"""HTTP/service boundary tests; scope and snapshot SQL runs in PGlite."""
from contextlib import contextmanager
from dataclasses import replace
import json
import unittest
from unittest.mock import Mock
from flask import Flask
from api_v1 import AccessState, Identity, install_api_v1
from v1_final_reports import FinalReportService, validate_final_report

USER='00000000-0000-4000-8000-000000000001'
SESSION='00000000-0000-4000-8000-000000000002'
KEY='fictional-final-request-001'
BODY={'summary':' Observations across screenings ', 'conclusion':'Expert conclusion',
      'next_steps':'Classroom support', 'expected_revision':0,'history_fingerprint':'a'*64}


class FinalReportTests(unittest.TestCase):
    def setUp(self):
        self.state=AccessState(USER,'Fictional expert','expert','active',False,'test','test')
        self.result={'code':None,'data':{'state':'Monitoring'}}
        self.executions=[]
        @contextmanager
        def connect():
            cursor=Mock();cursor.execute.side_effect=lambda *args:self.executions.append(args)
            cursor.fetchone.side_effect=lambda:{'result':self.result}
            connection=Mock();connection.cursor.return_value.__enter__=Mock(return_value=cursor)
            connection.cursor.return_value.__exit__=Mock(return_value=False)
            yield connection
        self.repository=Mock();self.repository.execute.side_effect=lambda *args:{'result':self.result}
        backend=Mock();backend.authenticate.return_value=Identity(USER,SESSION)
        backend.load_access.side_effect=lambda identity:self.state
        backend.final_report_service=FinalReportService(connect,self.repository)
        app=Flask(__name__);install_api_v1(app,backend);self.client=app.test_client()
        self.headers={'Authorization':'Bearer fictional','Idempotency-Key':KEY}

    def get(self,path='/students/9/final-report',headers=None):
        return self.client.get('/api/v1'+path,headers=self.headers if headers is None else headers)

    def post(self,body=None,headers=None,path='/students/9/final-report'):
        return self.client.post('/api/v1'+path,headers=self.headers if headers is None else headers,json=BODY if body is None else body)

    def test_read_binds_actor_session_and_target_and_is_private(self):
        response=self.get();self.assertEqual(response.status_code,200)
        self.assertEqual(self.executions[0][1],(USER,SESSION,'9'))
        self.assertEqual(response.headers['Cache-Control'],'no-store')

    def test_only_expert_can_finalize_even_with_valid_payload(self):
        for role in ['teacher','parent','admin','researcher','guest']:
            self.state=replace(self.state,role=role)
            self.assertEqual(self.post().status_code,403,role)
        self.repository.execute.assert_not_called()

    def test_authentication_and_onboarding_precede_reads_and_writes(self):
        self.assertEqual(self.get(headers={}).status_code,401)
        self.assertEqual(self.post(headers={}).status_code,401)
        original=self.state
        for changes in [{'must_change_password':True},{'accepted_agreement_version':None},{'account_status':'disabled'}]:
            self.state=replace(original,**changes)
            self.assertEqual(self.get().status_code,403)
            self.assertEqual(self.post().status_code,403)
        self.assertEqual(self.executions,[]);self.repository.execute.assert_not_called()

    def test_missing_and_inaccessible_have_same_response(self):
        self.result={'code':'NOT_FOUND'}
        self.assertEqual(self.get().status_code,404)
        self.assertEqual(self.post().status_code,404)

    def test_revision_fingerprint_text_and_untrusted_fields_rejected(self):
        for change in [{'summary':' '},{'summary':None},{'conclusion':'x'*10001},
                       {'next_steps':'nul\0value'},{'expected_revision':True},{'expected_revision':-1},
                       {'expected_revision':9223372036854775807},{'history_fingerprint':'wrong'},
                       {'expert_id':USER},{'screenings':[]},{'student_id':'9'}]:
            self.assertEqual(self.post({**BODY,**change}).status_code,422,change.keys())
        self.repository.execute.assert_not_called()

    def test_invalid_target_query_and_missing_key_rejected_before_database(self):
        for path in ['/students/01/final-report','/students/0/final-report','/students/9223372036854775808/final-report','/students/9/final-report?limit=1']:
            self.assertIn(self.get(path).status_code,[400,422])
            self.assertIn(self.post(path=path).status_code,[400,422])
        self.assertEqual(self.post(headers={'Authorization':'Bearer fictional'}).status_code,422)
        self.assertEqual(self.executions,[]);self.repository.execute.assert_not_called()

    def test_finalize_uses_writer_and_keeps_exact_retry_identity(self):
        for _ in range(2):self.assertEqual(self.post().status_code,200)
        sql,args=self.repository.execute.call_args.args
        self.assertIn('graphiscan_finalize_report',sql)
        self.assertEqual(args[:3],(USER,SESSION,'9'))
        self.assertEqual(args[4],KEY)
        self.assertEqual(json.loads(args[3])['summary'],'Observations across screenings')
        self.assertEqual(validate_final_report(BODY,KEY)['expected_revision'],0)

    def test_conflicts_and_not_ready_return_recoverable_status(self):
        for code in ['REVISION_CONFLICT','IDEMPOTENCY_CONFLICT','FINAL_REPORT_NOT_READY']:
            self.result={'code':code}
            response=self.post();self.assertEqual(response.status_code,409)
            self.assertEqual(response.json['error']['code'],code)

    def test_unknown_or_malformed_backend_result_fails_closed(self):
        for result in [{'code':'private_database_error'},{'code':None,'data':None}]:
            self.result=result;response=self.get();self.assertEqual(response.status_code,503)
            self.assertNotIn('private_database_error',response.get_data(as_text=True))


if __name__=='__main__':unittest.main()
