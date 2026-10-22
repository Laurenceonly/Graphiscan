"""Issuance saga safety; all identities and provider calls are mocks."""
import json
import unittest
from unittest.mock import Mock

from api_v1 import ApiError, Identity
from v1_account_issuance import AccountIssuanceService

ACTOR = '00000000-0000-4000-8000-000000000001'
SESSION = '00000000-0000-4000-8000-000000000002'
TARGET = '00000000-0000-4000-8000-000000000003'
KEY = '00000000-0000-4000-8000-000000000004'
REQUEST = '00000000-0000-4000-8000-000000000005'


class AccountIssuanceTests(unittest.TestCase):
    def setUp(self):
        self.repo, self.provider = Mock(), Mock()
        self.service = AccountIssuanceService(self.repo, self.provider)
        self.identity = Identity(ACTOR, SESSION)
        self.body = {'full_name': 'Fictional Account', 'email': 'fixture@example.invalid',
                     'role': 'teacher', 'school_ids': ['1'], 'temporary_password': 'FictionalTemporary!42'}
        self.receipt = {'user_id': TARGET, 'must_change_password': True}
        self.repo.execute.side_effect = [
            {'result': {'code': None, 'reserved': True}},
            {'result': {'code': None, 'data': self.receipt}},
        ]
        self.provider.create.return_value = TARGET

    def create(self, body=None):
        return self.service.create(self.identity, self.body if body is None else body, KEY, REQUEST)

    def test_reserves_before_provider_and_never_sends_password_to_database(self):
        events = []
        self.repo.execute.side_effect = lambda sql, params: (
            events.append('reserve' if 'begin_account' in sql else 'complete') or
            {'result': {'code': None, **({'reserved': True} if 'begin_account' in sql else {'data': self.receipt})}})
        self.provider.create.side_effect = lambda *args: events.append('provider') or TARGET
        self.assertEqual(self.create()['data'], self.receipt)
        self.assertEqual(events, ['reserve', 'provider', 'complete'])
        self.assertNotIn(self.body['temporary_password'], str(self.repo.execute.call_args_list))
        reservation_fields = json.loads(self.repo.execute.call_args_list[0].args[1][3])
        self.assertNotIn('temporary_password', reservation_fields)

    def test_pending_or_completed_reservation_never_calls_provider(self):
        self.repo.execute.side_effect = None
        self.repo.execute.return_value = {'result': {'code': 'ACCOUNT_CREATION_PENDING'}}
        with self.assertRaises(ApiError) as failure:
            self.create()
        self.assertEqual(failure.exception.code, 'ACCOUNT_CREATION_PENDING')
        self.provider.create.assert_not_called()
        self.repo.execute.return_value = {'result': {'code': None, 'data': self.receipt}}
        self.assertEqual(self.create()['data'], self.receipt)
        self.provider.create.assert_not_called()

    def test_provider_failure_preserves_reservation_without_completion_or_retry(self):
        self.provider.create.side_effect = RuntimeError('private provider text')
        with self.assertRaises(ApiError) as failure:
            self.create()
        self.assertEqual(failure.exception.code, 'ACCOUNT_CREATION_PENDING')
        self.assertNotIn('private provider text', str(failure.exception))
        self.assertEqual(self.repo.execute.call_count, 1)
        self.provider.create.assert_called_once()

    def test_profile_commit_failure_does_not_delete_or_retry_auth_identity(self):
        self.repo.execute.side_effect = [
            {'result': {'code': None, 'reserved': True}}, RuntimeError('private database text')]
        with self.assertRaises(ApiError) as failure:
            self.create()
        self.assertEqual(failure.exception.code, 'ACCOUNT_CREATION_PENDING')
        self.provider.create.assert_called_once()
        self.assertEqual(self.provider.method_calls[0][0], 'create')
        self.assertEqual(len(self.provider.method_calls), 1)

    def test_validation_and_database_denial_happen_before_provider(self):
        with self.assertRaises(ApiError):
            self.create({**self.body, 'temporary_password': 'weak'})
        self.repo.execute.assert_not_called()
        self.repo.execute.side_effect = None
        self.repo.execute.return_value = {'result': {'code': 'FORBIDDEN'}}
        with self.assertRaises(ApiError) as failure:
            self.create()
        self.assertEqual(failure.exception.code, 'FORBIDDEN')
        self.provider.create.assert_not_called()


if __name__ == '__main__':
    unittest.main()
