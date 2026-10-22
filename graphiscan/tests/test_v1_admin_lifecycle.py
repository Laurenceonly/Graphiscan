"""Credential saga boundaries with mocked provider/DB; no configuration or network."""
import unittest
from unittest.mock import Mock

import requests
from flask import Flask

from api_v1 import AccessState, ApiError, Grant, Identity, install_api_v1
from v1_admin_lifecycle import AdminLifecycleService

ACTOR = '00000000-0000-4000-8000-000000000001'
SESSION = '00000000-0000-4000-8000-000000000002'
TARGET = '00000000-0000-4000-8000-000000000003'
OPERATION = '00000000-0000-4000-8000-000000000004'


class AdminLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.reader, self.writer = Mock(), Mock()
        self.provider, self.password_provider = Mock(), Mock()
        self.provider.origin = 'https://fixture.invalid'
        self.provider.secret = 'synthetic-server-key'
        self.response = Mock(status_code=200)
        self.response.json.return_value = {'id': TARGET}
        self.provider.http.request.return_value = self.response
        self.receipt = {'user_id': TARGET, 'must_change_password': True}
        self.writer.execute.side_effect = [
            {'result': {'code': None, 'reserved': True}},
            {'result': {'code': None, 'data': self.receipt}},
        ]
        self.service = AdminLifecycleService(self.reader, self.writer, self.provider, self.password_provider)
        self.backend = Mock()
        self.backend.authenticate.return_value = Identity(ACTOR, SESSION)
        self.backend.load_access.return_value = AccessState(ACTOR, 'Fictional admin', 'admin', 'active',
            False, 'fixture-v1', 'fixture-v1', grants=(Grant('accounts.manage'),))
        self.backend.admin_lifecycle_service = self.service
        app = Flask(__name__)
        install_api_v1(app, self.backend)
        self.client = app.test_client()
        self.headers = {'Authorization': 'Bearer synthetic', 'Idempotency-Key': OPERATION}
        self.body = {'expected_revision': 2, 'current_password': 'FictionalCurrent!42',
                     'temporary_password': 'FictionalTemporary!42'}

    def reset(self, **kwargs):
        return self.client.post('/api/v1/accounts/' + TARGET + '/temporary-password',
                                json=kwargs.get('body', self.body), headers=kwargs.get('headers', self.headers))

    def test_success_reauthenticates_then_reserves_calls_provider_and_completes(self):
        response = self.reset()
        self.assertEqual(response.status_code, 200)
        self.password_provider.verify_current.assert_called_once_with(Identity(ACTOR, SESSION),
            'synthetic', self.body['current_password'])
        self.assertEqual(self.writer.execute.call_count, 2)
        self.assertIn('begin_admin_account_operation', self.writer.execute.call_args_list[0].args[0])
        self.assertIn('complete_admin_account_operation', self.writer.execute.call_args_list[1].args[0])
        self.assertEqual(self.provider.http.request.call_args.args[0], 'PUT')
        self.assertEqual(self.provider.http.request.call_args.kwargs['json'],
                         {'password': self.body['temporary_password']})
        self.assertFalse(self.provider.http.request.call_args.kwargs['allow_redirects'])
        self.response.close.assert_called_once()
        for secret in (self.body['current_password'], self.body['temporary_password'], self.provider.secret):
            self.assertNotIn(secret, str(self.writer.execute.call_args_list))
            self.assertNotIn(secret, response.text)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_invalid_or_unauthenticated_input_never_reaches_reauthentication(self):
        self.assertEqual(self.reset(headers={}).status_code, 401)
        self.assertEqual(self.reset(body={**self.body, 'expected_revision': True}).status_code, 422)
        self.assertEqual(self.reset(body={**self.body, 'temporary_password': 'weak'}).status_code, 422)
        self.assertEqual(self.reset(headers={'Authorization': 'Bearer synthetic'}).status_code, 422)
        self.writer.execute.assert_not_called()
        self.provider.http.request.assert_not_called()
        self.password_provider.verify_current.assert_not_called()

    def test_wrong_current_password_does_not_reserve_or_change_target(self):
        self.password_provider.verify_current.side_effect = ApiError(422, 'INVALID_CURRENT_PASSWORD', 'Check your password.')
        self.assertEqual(self.reset().status_code, 422)
        self.writer.execute.assert_not_called()
        self.provider.http.request.assert_not_called()

    def test_unconfigured_action_does_not_reauthenticate(self):
        self.service.writer = None
        response = self.reset()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json['error']['code'], 'ACCOUNT_ACTION_UNAVAILABLE')
        self.password_provider.verify_current.assert_not_called()

    def test_pending_or_completed_reservation_never_replays_provider_write(self):
        self.writer.execute.side_effect = None
        self.writer.execute.return_value = {'result': {'code': 'ACCOUNT_OPERATION_PENDING'}}
        self.assertEqual(self.reset().status_code, 409)
        self.provider.http.request.assert_not_called()
        self.writer.execute.return_value = {'result': {'code': None, 'data': self.receipt}}
        self.assertEqual(self.reset().status_code, 200)
        self.provider.http.request.assert_not_called()

    def test_provider_timeout_preserves_pending_and_never_calls_completion(self):
        self.provider.http.request.side_effect = requests.Timeout('private provider response')
        response = self.reset()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json['error']['code'], 'ACCOUNT_OPERATION_PENDING')
        self.assertEqual(self.writer.execute.call_count, 1)
        self.provider.http.request.assert_called_once()
        self.assertNotIn('private provider response', response.text)

    def test_provider_identity_mismatch_or_completion_failure_remains_pending(self):
        self.response.json.return_value = {'id': ACTOR}
        self.assertEqual(self.reset().json['error']['code'], 'ACCOUNT_OPERATION_PENDING')
        self.assertEqual(self.writer.execute.call_count, 1)
        self.response.close.assert_called_once()
        self.writer.execute.reset_mock()
        self.writer.execute.side_effect = [
            {'result': {'code': None, 'reserved': True}}, RuntimeError('private database details')]
        self.response.json.return_value = {'id': TARGET}
        response = self.reset()
        self.assertEqual(response.json['error']['code'], 'ACCOUNT_OPERATION_PENDING')
        self.assertNotIn('private database details', response.text)

    def test_delete_requires_typed_confirmation_and_only_then_calls_delete(self):
        path = '/api/v1/accounts/' + TARGET
        body = {key: value for key, value in self.body.items() if key != 'temporary_password'}
        self.assertEqual(self.client.delete(path, json={**body, 'confirmation': 'yes'}, headers=self.headers).status_code, 422)
        self.provider.http.request.assert_not_called()
        self.response.status_code = 204
        response = self.client.delete(path, json={**body, 'confirmation': 'DELETE'}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.provider.http.request.call_args.args[0], 'DELETE')
        self.assertEqual(self.provider.http.request.call_args.kwargs['json'], {'should_soft_delete': False})

    def test_operation_reads_use_reader_and_actor_session(self):
        self.reader.execute.return_value = {'result': {'code': None, 'data': {
            'operation_id': OPERATION, 'state': 'pending', 'action': 'reset_password', 'target_id': TARGET}}}
        response = self.client.get('/api/v1/account-operations/' + OPERATION, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.reader.execute.call_args.args[1], (ACTOR, SESSION, OPERATION))
        self.writer.execute.assert_not_called()
        self.provider.http.request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
