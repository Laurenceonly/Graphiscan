"""Synthetic Flask/reader/writer tests only; no hosted state or real notice approval."""
from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock, Mock

from flask import Flask, jsonify
from api_v1 import AccessState, ApiError, BackendUnavailable, Identity, InvalidSession, install_api_v1, require_access
from v1_privacy import PrivacyService, validate_acceptance

USER='00000000-0000-4000-8000-000000000001'
SESSION='00000000-0000-4000-8000-000000000002'
IDENTITY=Identity(USER,SESSION)
STAMP=datetime(2026,10,20,tzinfo=timezone.utc)


class PrivacyRouteTests(unittest.TestCase):
    def setUp(self):
        self.backend=Mock()
        self.backend.authenticate.return_value=IDENTITY
        self.backend.load_access.return_value=AccessState(USER,'Fictional','admin','active',False)
        self.backend.privacy_service.get_agreement.return_value=dict(version='test-v1',title='Test only',content='Fictional test',published_at=STAMP.isoformat())
        self.backend.privacy_service.accept.return_value=dict(agreement_version='test-v1',accepted_at=STAMP.isoformat())
        app=Flask(__name__)
        install_api_v1(app,self.backend)
        app.add_url_rule('/api/v1/probe','api_v1.probe',require_access()(lambda: jsonify(data={'ok':True})))
        self.client=app.test_client()
        self.headers={'Authorization':'Bearer synthetic'}

    def get(self):
        return self.client.get('/api/v1/privacy-agreement',headers=self.headers)

    def accept(self, body=None):
        return self.client.post('/api/v1/me/privacy-acceptance',headers=self.headers,
                                json=body if body is not None else {'agreement_version':'test-v1','accepted':True})

    def test_get_and_accept_allowed_before_privacy_but_not_before_password(self):
        self.assertEqual(self.get().status_code,200)
        self.assertEqual(self.accept().status_code,200)
        self.backend.load_access.return_value=AccessState(USER,'Fictional','admin','active',True)
        self.backend.privacy_service.reset_mock()
        for response in (self.get(),self.accept()):
            self.assertEqual(response.status_code,403)
            self.assertEqual(response.json['error']['code'],'PASSWORD_CHANGE_REQUIRED')
        self.backend.privacy_service.get_agreement.assert_not_called()
        self.backend.privacy_service.accept.assert_not_called()

    def test_inactive_revoked_missing_and_other_profiles_denied(self):
        for state in (None,AccessState(USER,'Fictional','teacher','disabled',False),
                      AccessState(SESSION,'Other','teacher','active',False)):
            self.backend.load_access.return_value=state
            self.assertEqual(self.get().status_code,403)
            self.assertEqual(self.accept().status_code,403)
        self.backend.load_access.side_effect=InvalidSession()
        self.assertEqual(self.accept().status_code,401)
        self.backend.privacy_service.accept.assert_not_called()

    def test_accept_body_requires_exact_version_true_and_no_client_identity_or_time(self):
        for body in ({},[],{'agreement_version':'test-v1','accepted':False},
                     {'agreement_version':'test-v1','accepted':1},
                     {'agreement_version':'','accepted':True},
                     {'agreement_version':'test-v1','accepted':True,'user_id':SESSION}):
            self.assertEqual(self.accept(body).status_code,422)
        response=self.client.post('/api/v1/me/privacy-acceptance',headers=self.headers,data='x'*5000,content_type='application/json')
        self.assertEqual(response.status_code,413)
        self.backend.privacy_service.accept.assert_not_called()

    def test_success_response_uses_server_service_identity_and_no_store(self):
        response=self.accept()
        args=self.backend.privacy_service.accept.call_args.args
        self.assertEqual(args,(IDENTITY,'test-v1',response.json['request_id']))
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(set(response.json['data']),{'agreement_version','accepted_at'})

    def test_missing_notice_and_service_fail_closed(self):
        self.backend.privacy_service.get_agreement.side_effect=ApiError(503,'AGREEMENT_NOT_CONFIGURED','Unavailable')
        self.assertEqual(self.get().status_code,503)
        self.backend.privacy_service=None
        self.assertEqual(self.accept().status_code,503)

    def test_bootstrap_gate_rechecks_revision_and_acceptance_on_each_request(self):
        self.backend.load_access.return_value=AccessState(USER,'Fictional','teacher','active',False,'v1',None)
        self.assertEqual(self.client.get('/api/v1/probe',headers=self.headers).status_code,403)
        self.backend.load_access.return_value=AccessState(USER,'Fictional','teacher','active',False,'v1','v1')
        self.assertEqual(self.client.get('/api/v1/probe',headers=self.headers).status_code,200)
        self.backend.load_access.return_value=AccessState(USER,'Fictional','teacher','active',False,'v2','v1')
        self.assertEqual(self.client.get('/api/v1/probe',headers=self.headers).status_code,403)


class PrivacyServiceTests(unittest.TestCase):
    def setUp(self):
        self.connect=MagicMock()
        self.cursor=self.connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        self.writer=Mock()
        self.service=PrivacyService(self.connect,self.writer)

    def test_reader_only_projects_notice_with_subject_parameter(self):
        self.cursor.fetchone.return_value=dict(version='v1',title='Test',content='Fictional',published_at=STAMP,approved_by='private')
        result=self.service.get_agreement(IDENTITY)
        self.assertEqual(set(result),{'version','title','content','published_at'})
        self.assertEqual(self.cursor.execute.call_args.args[1],(USER,))
        self.writer.execute.assert_not_called()

    def test_absent_unpublished_or_corrupt_notice_unavailable(self):
        self.cursor.fetchone.return_value=None
        with self.assertRaises(ApiError) as error:
            self.service.get_agreement(IDENTITY)
        self.assertEqual(error.exception.code,'AGREEMENT_NOT_CONFIGURED')

    def test_atomic_writer_results_map_to_contract_errors(self):
        for outcome,kind,code in [('invalid_session',InvalidSession,None),
            ('account_unavailable',ApiError,'ACCOUNT_UNAVAILABLE'),('password_required',ApiError,'PASSWORD_CHANGE_REQUIRED'),
            ('agreement_unavailable',ApiError,'AGREEMENT_NOT_CONFIGURED'),('agreement_changed',ApiError,'AGREEMENT_CHANGED'),
            ('unexpected',BackendUnavailable,None)]:
            with self.subTest(outcome=outcome):
                self.writer.execute.return_value={'outcome':outcome}
                with self.assertRaises(kind) as error:
                    self.service.accept(IDENTITY,'v1',USER)
                if code:
                    self.assertEqual(error.exception.code,code)

    def test_accepted_timestamp_and_subject_session_binding(self):
        self.writer.execute.return_value=dict(outcome='accepted',agreement_version='v1',accepted_at=STAMP)
        self.assertEqual(self.service.accept(IDENTITY,'v1',USER),dict(agreement_version='v1',accepted_at=STAMP.isoformat()))
        self.assertEqual(self.writer.execute.call_args.args[1],(USER,SESSION,'v1',USER))
        self.writer.execute.return_value['agreement_version']='v2'
        with self.assertRaises(BackendUnavailable):
            self.service.accept(IDENTITY,'v1',USER)

    def test_missing_writer_and_naive_timestamp_deny(self):
        with self.assertRaises(BackendUnavailable):
            PrivacyService(self.connect).accept(IDENTITY,'v1',USER)
        self.writer.execute.return_value=dict(outcome='accepted',agreement_version='v1',accepted_at=datetime(2026,10,20))
        with self.assertRaises(BackendUnavailable):
            self.service.accept(IDENTITY,'v1',USER)
