"""HTTP/service validation; PostgreSQL role/scope rules are exercised in PGlite."""
import unittest
from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import Mock
from flask import Flask
from api_v1 import AccessState, Identity, install_api_v1
from v1_screenings import ScreeningReadService

USER='00000000-0000-4000-8000-000000000001'
SESSION='00000000-0000-4000-8000-000000000002'
STAMP='2026-01-01T00:00:00+00:00'

class ScreeningTests(unittest.TestCase):
    def setUp(self):
        self.state=AccessState(USER,'Fictional teacher','teacher','active',False,'test','test')
        self.result={'code':None,'rows':[],'found':True}
        self.executions=[]
        self.failure=False
        @contextmanager
        def connect():
            if self.failure: raise RuntimeError('private SQL DSN')
            cursor=Mock()
            cursor.execute.side_effect=lambda *args:self.executions.append(args)
            cursor.fetchone.side_effect=lambda:{'result':self.result}
            connection=Mock()
            connection.cursor.return_value.__enter__=Mock(return_value=cursor)
            connection.cursor.return_value.__exit__=Mock(return_value=False)
            yield connection
        self.service=ScreeningReadService(connect,cursor_key=b'x'*32,now=lambda:1000)
        self.backend=Mock()
        self.backend.authenticate.return_value=Identity(USER,SESSION)
        self.backend.load_access.side_effect=lambda identity:self.state
        self.backend.screening_read_service=self.service
        app=Flask(__name__);install_api_v1(app,self.backend)
        self.client=app.test_client()
    def get(self,path='/screenings',authenticated=True):
        return self.client.get('/api/v1'+path,headers={'Authorization':'Bearer fictional'} if authenticated else {})
    def test_authentication_role_and_onboarding_precede_record_queries(self):
        self.assertEqual(self.get(authenticated=False).status_code,401)
        original=self.state
        for changes,status in [({'role':'guest'},403),({'must_change_password':True},403),({'account_status':'disabled'},403),({'accepted_agreement_version':None},403)]:
            self.state=replace(original,**changes)
            self.assertEqual(self.get().status_code,status)
        self.assertEqual(self.executions,[])
    def test_empty_list_and_linked_empty_history(self):
        for path in ['/screenings','/students/1/history']:
            response=self.get(path)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json['data'],[])
            self.assertEqual(response.headers['Cache-Control'],'no-store')
    def test_detail_report_and_unlinked_history_have_private_not_found(self):
        self.assertEqual(self.get('/screenings/1').status_code,404)
        self.assertEqual(self.get('/reports/1').status_code,404)
        self.result['found']=False
        self.assertEqual(self.get('/students/1/history').status_code,404)
    def test_invalid_filters_rejected_without_database(self):
        for query in ['limit=0','limit=101','limit=01','student_id=0','model_id=9223372036854775808','grade_level=4','validation_status=anything','task_type=anything','from=2026-01-01','from=infinity','from=2026-01-01T00:00:00','from=2026-02-01T00:00:00Z&to=2026-01-01T00:00:00Z','student_id=1&student_id=2','teacher_id=1','order=oldest','cursor=wrong']:
            self.assertEqual(self.get('/screenings?'+query).status_code,422,query)
        for path in ['/screenings/01','/screenings/1?limit=1','/reports/0','/students/1/history?order=wrong','/students/1/history?school_id=1']:
            self.assertEqual(self.get(path).status_code,422,path)
        self.assertEqual(self.executions,[])
    def test_filters_are_bound_and_dates_are_timezone_normalized(self):
        response=self.get('/screenings?student_id=9&validation_status=Validated&from=2026-01-01T08:00:00%2B08:00')
        self.assertEqual(response.status_code,200)
        sql,args=self.executions[-1]
        self.assertNotIn('Validated',sql)
        self.assertIn('2026-01-01T00:00:00+00:00',args[3])
        self.assertEqual(args[:3],(USER,SESSION,'screenings'))
    def test_cursor_binds_student_order_filters_and_session(self):
        self.result['rows']=[{'result_id':'2','date_generated':STAMP},{'result_id':'3','date_generated':STAMP}]
        response=self.get('/students/1/history?limit=1&order=oldest')
        token=response.json['page']['next_cursor']
        self.assertEqual(len(response.json['data']),1)
        self.assertEqual(self.get('/students/1/history?limit=1&order=oldest&cursor='+token).status_code,200)
        for path in ['/students/2/history?limit=1&order=oldest','/students/1/history?limit=1&order=newest','/screenings?limit=1']:
            self.assertEqual(self.get(path+'&cursor='+token).status_code,422)
    def test_current_database_gates_override_earlier_http_authorization(self):
        for code,status in [('AUTHENTICATION_REQUIRED',401),('PRIVACY_ACCEPTANCE_REQUIRED',403),('AGREEMENT_NOT_CONFIGURED',503),('PASSWORD_CHANGE_REQUIRED',403)]:
            self.result={'code':code,'rows':[]}
            self.assertEqual(self.get().status_code,status)
    def test_failures_are_sanitized(self):
        self.failure=True
        response=self.get()
        self.assertEqual(response.status_code,503)
        self.assertNotIn('private',response.get_data(as_text=True))

if __name__=='__main__':unittest.main()
