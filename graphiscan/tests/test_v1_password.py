"""Fictional credentials and mock HTTP/DB only; never contact configured services."""
import unittest
from unittest.mock import Mock

import requests
from flask import Flask

from api_v1 import AccessState, ApiError, BackendUnavailable, Identity, InvalidSession, install_api_v1
from v1_password import (PasswordService, PostgresPasswordRepository,
                         SupabasePasswordProvider, validate_password_change)
from tools.recover_v1_password import recover, TEST_EMAIL

USER = '00000000-0000-4000-8000-000000000001'
SESSION = '00000000-0000-4000-8000-000000000002'
OTHER = '00000000-0000-4000-8000-000000000003'
IDENTITY = Identity(USER, SESSION)
BODY = dict(current_password='Synthetic-old-1', new_password='Synthetic-new-2', confirm_password='Synthetic-new-2')


class PasswordRouteTests(unittest.TestCase):
    def setUp(self):
        self.backend = Mock()
        self.backend.authenticate.return_value = IDENTITY
        self.backend.load_access.return_value = AccessState(USER, 'Fictional', 'teacher', 'active', True)
        app = Flask(__name__)
        install_api_v1(app, self.backend)
        self.client = app.test_client()

    def post(self, **kwargs):
        return self.client.post('/api/v1/me/password', headers={'Authorization': 'Bearer synthetic'}, **kwargs)

    def test_first_login_bypasses_only_onboarding_and_returns_no_secrets(self):
        response = self.post(json=BODY)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['data'], dict(success=True, next_action='sign_in'))
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        args = self.backend.password_service.change.call_args.args
        self.assertEqual(args[:4], (IDENTITY, 'synthetic', BODY['current_password'], BODY['new_password']))
        self.assertEqual(args[4], response.json['request_id'])

    def test_disabled_or_missing_profile_cannot_change_password(self):
        for state in (None, AccessState(USER, 'Fictional', 'teacher', 'disabled', True)):
            self.backend.load_access.return_value = state
            self.assertEqual(self.post(json=BODY).status_code, 403)
        self.backend.password_service.change.assert_not_called()

    def test_revoked_session_and_missing_bearer_denied(self):
        self.backend.load_access.side_effect = InvalidSession()
        self.assertEqual(self.post(json=BODY).status_code, 401)
        self.assertEqual(self.client.post('/api/v1/me/password', json=BODY).status_code, 401)
        self.backend.password_service.change.assert_not_called()

    def test_no_writer_configuration_returns_503(self):
        self.backend.password_service = None
        self.assertEqual(self.post(json=BODY).status_code, 503)

    def test_invalid_json_fields_and_large_requests_do_not_call_service(self):
        cases = [None, [], {}, {**BODY, 'user_id': OTHER}, {**BODY, 'current_password': 12},
                 {**BODY, 'new_password': 'weak'}, {**BODY, 'confirm_password': 'mismatch'},
                 {**BODY, 'current_password': BODY['new_password']}]
        for body in cases:
            self.assertIn(self.post(json=body).status_code, (400, 422))
        self.assertEqual(self.post(data='{invalid', content_type='application/json').status_code, 422)
        self.assertEqual(self.post(data='x'*17000, content_type='application/json').status_code, 413)
        self.backend.password_service.change.assert_not_called()

    def test_ready_account_can_change_password(self):
        self.backend.load_access.return_value = AccessState(USER, 'Fictional', 'teacher', 'active', False, 'v1', 'v1')
        self.assertEqual(self.post(json=BODY).status_code, 200)

    def test_errors_are_sanitized(self):
        self.backend.password_service.change.side_effect = RuntimeError('private DSN/password')
        response = self.post(json=BODY)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('private', response.get_data(as_text=True))


class PasswordServiceTests(unittest.TestCase):
    def setUp(self):
        self.events = Mock()
        self.provider, self.repository = Mock(), Mock()
        self.events.attach_mock(self.provider, 'provider')
        self.events.attach_mock(self.repository, 'repository')
        self.service = PasswordService(self.provider, self.repository)

    def change(self):
        self.service.change(IDENTITY, 'synthetic', BODY['current_password'], BODY['new_password'], OTHER)

    def test_commit_order_and_operation_binding(self):
        self.change()
        self.assertEqual([c[0] for c in self.events.mock_calls], [
            'provider.verify_current', 'repository.begin', 'provider.update',
            'provider.sign_out_all', 'repository.complete'])
        self.assertEqual(self.repository.begin.call_args.args[1], self.repository.complete.call_args.args[1])

    def test_wrong_password_does_not_begin_or_update(self):
        self.provider.verify_current.side_effect = ApiError(422, 'CURRENT_PASSWORD_INVALID', 'Denied')
        with self.assertRaises(ApiError):
            self.change()
        self.repository.begin.assert_not_called()
        self.provider.update.assert_not_called()

    def test_uncertain_begin_commit_or_racing_revocation_never_updates_provider(self):
        for error in (BackendUnavailable(), InvalidSession()):
            self.repository.begin.side_effect = error
            with self.assertRaises(type(error)):
                self.change()
        self.provider.update.assert_not_called()

    def test_every_post_begin_failure_stays_pending_without_retry_or_compensation(self):
        for method in ('update', 'sign_out_all', 'complete'):
            with self.subTest(method=method):
                self.setUp()
                target = self.repository if method == 'complete' else self.provider
                getattr(target, method).side_effect = RuntimeError('private provider error')
                with self.assertRaises(ApiError) as caught:
                    self.change()
                self.assertEqual(caught.exception.code, 'PASSWORD_CHANGE_RECOVERY_REQUIRED')
                self.assertNotIn('private', caught.exception.message)
                getattr(target, method).assert_called_once()
                if method == 'update':
                    self.provider.sign_out_all.assert_not_called()
                if method != 'complete':
                    self.repository.complete.assert_not_called()


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.verifier = Mock(origin='https://synthetic.example.invalid', key='sb_publishable_synthetic')
        self.verifier.authenticate.return_value = Identity(USER, OTHER)
        self.http = Mock()
        self.provider = SupabasePasswordProvider(self.verifier, http=self.http)

    def response(self, status=200, body=None):
        response = Mock(status_code=status)
        response.json.return_value = body
        return response

    def test_current_password_uses_provider_email_and_verified_subject_then_local_cleanup(self):
        responses = [self.response(body={'id': USER, 'email': 'fiction@example.invalid'}),
                     self.response(body={'access_token': 'synthetic-token'}), self.response(204)]
        self.http.request.side_effect = responses
        self.provider.verify_current(IDENTITY, 'original', 'fictional-password')
        calls = self.http.request.call_args_list
        self.assertEqual(calls[1].kwargs['json'], {'email': 'fiction@example.invalid', 'password': 'fictional-password'})
        self.assertTrue(calls[2].args[1].endswith('/logout?scope=local'))
        self.assertEqual(calls[2].kwargs['headers']['Authorization'], 'Bearer synthetic-token')
        for response in responses:
            response.close.assert_called_once()

    def test_wrong_subject_still_cleans_extra_session(self):
        self.verifier.authenticate.return_value = Identity(OTHER, OTHER)
        self.http.request.side_effect = [self.response(body={'id': USER, 'email': 'fiction@example.invalid'}),
                                        self.response(body={'access_token': 'synthetic'}), self.response(204)]
        with self.assertRaises(BackendUnavailable):
            self.provider.verify_current(IDENTITY, 'original', 'fictional-password')
        self.assertTrue(self.http.request.call_args.args[1].endswith('scope=local'))

    def test_provider_password_denial_allowlist_and_redaction(self):
        for code, error in [('invalid_credentials', ApiError), ('unknown-private', BackendUnavailable)]:
            self.http.request.return_value = self.response(400, {'error_code': code, 'msg': 'private'})
            with self.assertRaises(error):
                self.provider.call('POST', '/token?grant_type=password')

    def test_timeout_redirect_rate_limit_and_malformed_json_never_retry(self):
        for status in (302, 500):
            self.http.reset_mock()
            self.http.request.return_value = self.response(status)
            with self.assertRaises(BackendUnavailable):
                self.provider.update(IDENTITY, 'original', 'old', 'new')
            self.http.request.assert_called_once()
            self.assertFalse(self.http.request.call_args.kwargs['allow_redirects'])
        self.http.request.side_effect = requests.Timeout('private')
        with self.assertRaises(BackendUnavailable):
            self.provider.sign_out_all('original')

    def test_update_subject_binding_and_global_scope(self):
        self.http.request.return_value = self.response(body={'id': OTHER})
        with self.assertRaises(BackendUnavailable):
            self.provider.update(IDENTITY, 'original', 'old', 'new')
        self.http.request.return_value = self.response(204)
        self.provider.sign_out_all('original')
        self.assertTrue(self.http.request.call_args.args[1].endswith('/logout?scope=global'))

    def test_database_exceptions_do_not_escape(self):
        repo = PostgresPasswordRepository(Mock(side_effect=RuntimeError('private DSN')))
        with self.assertRaises(BackendUnavailable) as error:
            repo.begin(IDENTITY, OTHER, OTHER)
        self.assertNotIn('private', str(error.exception))

    def test_strength_requires_each_contract_class_without_trimming_password(self):
        for new in ('abcdefgh1!', 'ABCDEFGH1!', 'Abcdefghi!', 'Abcdefghi1', 'Aa1!'):
            with self.assertRaises(ApiError):
                validate_password_change({**BODY, 'new_password': new, 'confirm_password': new})
        self.assertEqual(validate_password_change(BODY), (BODY['current_password'], BODY['new_password']))


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.backend = Mock()
        self.backend.authenticate.return_value = IDENTITY
        self.provider = self.backend.password_service.provider
        self.repo = self.backend.password_service.repository
        self.provider.call.side_effect = [{'access_token': 'synthetic'}, {'id': USER, 'email': TEST_EMAIL}]

    def test_recovery_verifies_new_password_and_global_logout_before_completion(self):
        events = Mock()
        events.attach_mock(self.provider, 'provider')
        events.attach_mock(self.repo, 'repo')
        self.assertTrue(recover(self.backend, OTHER, 'Synthetic-intended-new-2'))
        self.assertEqual([c[0] for c in events.mock_calls], ['provider.call', 'provider.call',
                                                          'provider.sign_out_all', 'repo.complete'])
        self.assertEqual(self.repo.complete.call_args.args[:2], (IDENTITY, OTHER))
        self.assertEqual(self.provider.call.call_args_list[0].kwargs['body']['email'], TEST_EMAIL)
        self.provider.update.assert_not_called()

    def test_wrong_email_cleans_session_and_does_not_complete(self):
        self.provider.call.side_effect = [{'access_token': 'synthetic'}, {'id': USER, 'email': 'other@example.invalid'}, None]
        self.assertFalse(recover(self.backend, OTHER, 'Synthetic-new-2'))
        self.repo.complete.assert_not_called()
        self.assertEqual(self.provider.call.call_args.args[1], '/logout?scope=local')

    def test_global_logout_or_completion_failure_does_not_claim_recovery(self):
        self.provider.sign_out_all.side_effect = BackendUnavailable()
        self.assertFalse(recover(self.backend, OTHER, 'Synthetic-new-2'))
        self.repo.complete.assert_not_called()
        self.setUp()
        self.repo.complete.side_effect = BackendUnavailable()
        self.assertFalse(recover(self.backend, OTHER, 'Synthetic-new-2'))

    def test_wrong_new_password_does_not_complete_or_update(self):
        self.provider.call.side_effect = ApiError(422, 'CURRENT_PASSWORD_INVALID', 'Denied')
        self.assertFalse(recover(self.backend, OTHER, 'Synthetic-wrong-1'))
        self.repo.complete.assert_not_called()
        self.provider.update.assert_not_called()
