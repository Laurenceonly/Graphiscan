"""Synthetic standalone endpoint-checker lifecycle; no provider/DB network."""
import unittest
from unittest.mock import Mock, patch

from api_v1 import AccessState, ApiError, Identity, InvalidSession
from v1_backend import SupabasePostgresBackend
from tools import check_v1_password as checker

USER = '00000000-0000-4000-8000-000000000001'
OLD = 'Synthetic-old-1'
NEW = 'Synthetic-new-2'


class PasswordCheckerTests(unittest.TestCase):
    def setUp(self):
        self.verifier, self.repository, self.service = Mock(), Mock(), Mock()
        self.backend = SupabasePostgresBackend(self.verifier, self.repository, self.service)
        self.provider = self.service.provider
        self.changed = False
        self.sessions, self.revoked = {}, set()

        def authenticate(token):
            return self.sessions[token]

        def access(identity):
            if identity.session_id in self.revoked:
                raise InvalidSession()
            return AccessState(USER, 'Synthetic Test Admin', 'admin', 'active', not self.changed)

        def call(method, path, **kwargs):
            if path == '/token?grant_type=password':
                self.assertEqual(kwargs['body']['email'], checker.TEST_EMAIL)
                password = kwargs['body']['password']
                if password != (NEW if self.changed else OLD):
                    raise ApiError(422, 'CURRENT_PASSWORD_INVALID', 'Denied')
                index = len(self.sessions) + 10
                token = 'synthetic-token-' + str(index)
                self.sessions[token] = Identity(USER, f'00000000-0000-4000-8000-{index:012d}')
                return {'access_token': token}
            if path == '/user':
                return {'id': USER, 'email': checker.TEST_EMAIL}
            if path == '/logout?scope=local':
                self.revoked.add(self.sessions[kwargs['bearer']].session_id)
                return None
            raise AssertionError('Unexpected synthetic operation')

        def change(identity, bearer, current, new, request_id):
            self.assertEqual((current, new), (OLD, NEW))
            self.changed = True
            self.revoked.update(identity.session_id for identity in self.sessions.values())

        self.verifier.authenticate.side_effect = authenticate
        self.repository.load_access.side_effect = access
        self.provider.call.side_effect = call
        self.service.change.side_effect = change

    def run_check(self, **kwargs):
        return checker.run_password_check(kwargs.get('current', OLD), NEW, NEW, self.backend)

    def test_success_exercises_endpoint_old_password_denial_two_sessions_fresh_signin_and_cleanup(self):
        report = self.run_check()
        self.assertEqual(report['status'], 'password-check-passed')
        self.assertTrue(all(row['status'] == 'pass' for row in report['checks']))
        self.assertTrue(report['application_writes_may_have_occurred'])
        self.assertEqual(len(self.sessions), 3)
        self.assertEqual(len(self.revoked), 3)
        self.assertNotIn(OLD, str(report))
        self.assertNotIn(NEW, str(report))
        self.assertNotIn('synthetic-token', str(report))

    def test_invalid_input_never_signs_in(self):
        report = checker.run_password_check(OLD, 'weak', 'weak', self.backend)
        self.assertEqual(report['status'], 'blocked')
        self.provider.call.assert_not_called()
        self.service.change.assert_not_called()

    def test_wrong_current_password_never_changes_and_does_not_retry(self):
        report = self.run_check(current='incorrect')
        self.assertNotEqual(report['status'], 'password-check-passed')
        self.provider.call.assert_called_once()
        self.service.change.assert_not_called()

    def test_already_changed_fixture_is_refused_and_sessions_cleaned(self):
        self.repository.load_access.side_effect = lambda identity: AccessState(USER, 'Synthetic Test Admin', 'admin', 'active', False)
        report = self.run_check()
        self.assertEqual(report['status'], 'failed')
        self.service.change.assert_not_called()
        self.assertEqual(len(self.revoked), 2)

    def test_endpoint_failure_does_not_retry_and_cleans_provider_sessions_despite_app_denial(self):
        def fail(*args):
            self.revoked.update(identity.session_id for identity in self.sessions.values())
            raise ApiError(503, 'PASSWORD_CHANGE_RECOVERY_REQUIRED', 'Contact administrator')
        self.service.change.side_effect = fail
        report = self.run_check()
        self.assertTrue(report['recovery_required'])
        self.assertEqual(report['status'], 'failed')
        self.service.change.assert_called_once()
        logouts = [call for call in self.provider.call.call_args_list if call.args[1] == '/logout?scope=local']
        self.assertEqual(len(logouts), 2)

    def test_wrong_provider_user_never_reaches_write(self):
        original_call = self.provider.call.side_effect
        self.provider.call.side_effect = lambda method, path, **kwargs: (
            {'id': USER, 'email': 'other@example.invalid'} if path == '/user' else original_call(method,path,**kwargs))
        report = self.run_check()
        self.assertNotEqual(report['status'], 'password-check-passed')
        self.service.change.assert_not_called()
        self.assertEqual(len(self.revoked), 1)

    def test_cleanup_failure_is_not_success(self):
        original_call = self.provider.call.side_effect
        def call(method,path,**kwargs):
            if path == '/logout?scope=local':
                raise RuntimeError('private-provider-error')
            return original_call(method,path,**kwargs)
        self.provider.call.side_effect = call
        report = self.run_check()
        self.assertEqual(report['status'], 'failed')
        self.assertNotIn('private', str(report))

    def test_no_writer_and_noninteractive_input_are_blocked(self):
        self.backend.password_service = None
        self.assertEqual(self.run_check()['status'], 'blocked')
        with patch.object(checker.sys, 'argv', ['check']), patch.object(checker.sys.stdin, 'isatty', return_value=False), \
                patch.object(checker.getpass, 'getpass') as prompt, patch('builtins.print'):
            self.assertEqual(checker.main(), 2)
            prompt.assert_not_called()
