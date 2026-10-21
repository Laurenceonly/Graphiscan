"""Synthetic session endpoints, provider responses and repository only."""
import unittest
from unittest.mock import Mock
from flask import Flask
from api_v1 import AccessState, ApiError, BackendUnavailable, Identity, InvalidSession, install_api_v1
from v1_sessions import SessionService

USER='00000000-0000-4000-8000-000000000001'
SESSION='00000000-0000-4000-8000-000000000002'


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.backend,self.provider,self.writer=Mock(),Mock(),Mock()
        self.backend.authenticate.return_value=Identity(USER,SESSION)
        self.backend.load_access.return_value=AccessState(USER,'Synthetic','admin','active',True)
        self.provider.call.return_value=dict(access_token='synthetic-access',refresh_token='synthetic-refresh',token_type='bearer',expires_in=3600)
        self.service=SessionService(self.backend,self.provider,self.writer)
        self.backend.session_service=self.service
        self.writer.execute.return_value={'ok':True}
        app=Flask(__name__);install_api_v1(app,self.backend)
        self.client=app.test_client()

    def login(self,body=None):
        return self.client.post('/api/v1/session/login',json=body or dict(email='fixture@example.invalid',password='synthetic'))

    def test_login_verifies_current_profile_and_allows_onboarding(self):
        response=self.login()
        self.assertEqual(response.status_code,200)
        self.assertEqual(set(response.json['data']),{'access_token','refresh_token','token_type','expires_in'})
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.backend.load_access.assert_called_once_with(Identity(USER,SESSION))
        self.assertEqual(self.provider.call.call_args.args[1],'/token?grant_type=password')

    def test_client_identity_role_fields_rejected_before_provider(self):
        for body in (dict(email='x@y',password='p',role='admin'),dict(email='x@y',password=''),dict(email=12,password='p')):
            self.assertEqual(self.login(body).status_code,422)
        self.provider.call.assert_not_called()

    def test_bad_credentials_rate_limit_and_backend_outage_are_fixed_errors(self):
        for error,status in [(ApiError(422,'CURRENT_PASSWORD_INVALID','Denied'),401),
                             (ApiError(429,'RATE_LIMITED','Wait'),429),(BackendUnavailable(),503)]:
            self.provider.call.side_effect=error
            self.assertEqual(self.login().status_code,status)

    def test_missing_disabled_or_mismatched_profile_cleans_issued_session(self):
        for state in (None,AccessState(USER,'Synthetic','admin','disabled',False),
                      AccessState(SESSION,'Other','admin','active',False)):
            self.backend.load_access.return_value=state
            response=self.login()
            self.assertEqual(response.status_code,403)
            self.assertEqual(self.provider.call.call_args.args[1],'/logout?scope=local')

    def test_refresh_revoked_pending_or_missing_session_does_not_return_tokens(self):
        self.backend.load_access.side_effect=InvalidSession()
        response=self.client.post('/api/v1/session/refresh',json={'refresh_token':'synthetic-refresh'})
        self.assertEqual(response.status_code,401)
        self.assertNotIn('synthetic-access',response.get_data(as_text=True))
        self.assertEqual(self.provider.call.call_args.args[1],'/logout?scope=local')

    def test_refresh_validates_exact_fields_and_provider_identity(self):
        response=self.client.post('/api/v1/session/refresh',json={'refresh_token':'synthetic-refresh'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.provider.call.call_args.args[1],'/token?grant_type=refresh_token')
        self.assertEqual(self.client.post('/api/v1/session/refresh',json={'refresh_token':'x','user_id':USER}).status_code,422)

    def test_malformed_provider_result_is_not_returned_and_known_token_is_cleaned(self):
        for field,value in [('expires_in',True),('expires_in',0),('refresh_token',None),('token_type','other')]:
            self.provider.call.return_value=dict(access_token='synthetic-access',refresh_token='synthetic-refresh',token_type='bearer',expires_in=3600)
            self.provider.call.return_value[field]=value
            self.assertEqual(self.login().status_code,503)
            self.assertEqual(self.provider.call.call_args.args[1],'/logout?scope=local')

    def test_logout_bypasses_account_and_password_gates_but_not_authentication(self):
        response=self.client.post('/api/v1/session/logout',headers={'Authorization':'Bearer synthetic-access'})
        self.assertEqual(response.status_code,200)
        self.backend.load_access.assert_not_called()
        self.assertEqual(self.writer.execute.call_args.args[1][:2],(USER,SESSION))
        self.assertEqual(self.client.post('/api/v1/session/logout').status_code,401)

    def test_logout_durable_commit_precedes_provider_and_outage_stays_denied(self):
        events=Mock();events.attach_mock(self.writer,'writer');events.attach_mock(self.provider,'provider')
        self.provider.call.side_effect=BackendUnavailable()
        response=self.client.post('/api/v1/session/logout',headers={'Authorization':'Bearer synthetic-access'})
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json['error']['code'],'PROVIDER_SIGNOUT_PENDING')
        self.assertEqual([call[0] for call in events.mock_calls],['writer.execute','provider.call'])

    def test_uncertain_revocation_commit_prevents_provider_call(self):
        self.writer.execute.side_effect=BackendUnavailable()
        self.assertEqual(self.client.post('/api/v1/session/logout',headers={'Authorization':'Bearer synthetic-access'}).status_code,503)
        self.provider.call.assert_not_called()

    def test_unknown_backend_and_oversize_input_fail_closed(self):
        self.backend.session_service=None
        self.assertEqual(self.login().status_code,503)
        self.backend.session_service=self.service
        self.assertEqual(self.client.post('/api/v1/session/login',data='x'*25000,content_type='application/json').status_code,413)
