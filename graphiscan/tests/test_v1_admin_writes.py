"""Account-write input and access boundaries; all records are synthetic."""
import json
import unittest
from dataclasses import replace
from unittest.mock import Mock

from flask import Flask

from api_v1 import AccessState, ApiError, Grant, Identity, install_api_v1
from v1_admin_writes import AdminWriteService, validate_account_update

ACTOR = '00000000-0000-4000-8000-000000000001'
SESSION = '00000000-0000-4000-8000-000000000002'
TARGET = '00000000-0000-4000-8000-000000000003'


class AdminWriteTests(unittest.TestCase):
    def setUp(self):
        self.identity = Identity(ACTOR, SESSION)
        self.state = AccessState(ACTOR, 'Fictional admin', 'admin', 'active', False,
            'fixture-v1', 'fixture-v1', grants=(Grant('accounts.manage'),))
        self.repo = Mock()
        self.repo.execute.return_value = {'result': {'code': None, 'data': {
            'user_id': TARGET, 'full_name': 'Synthetic account', 'role': 'teacher',
            'account_status': 'active', 'revision': 3, 'school_ids': [],
            'permission_grants': [], 'permissions': [], 'created_at': '2026-10-21T00:00:00Z',
            'onboarding': {'must_change_password': True, 'required_agreement_version': 'fixture-v1',
                           'accepted_agreement_version': None, 'next_action': 'change_password'}}}}
        service = AdminWriteService(self.repo)
        self.backend = Mock()
        self.backend.authenticate.return_value = self.identity
        self.backend.load_access.side_effect = lambda identity: self.state
        self.backend.admin_write_service = service
        app = Flask(__name__)
        install_api_v1(app, self.backend)
        self.client = app.test_client()
        self.headers = {'Authorization': 'Bearer fictional'}

    def test_validates_and_normalizes_account_update(self):
        body = validate_account_update({'expected_revision': 1, 'full_name': '  Synthetic   User  ',
            'school_ids': ['2', '1'], 'permission_grants': [
                {'permission_key': 'assignments.manage', 'school_id': '2'}]})
        self.assertEqual(body['full_name'], 'Synthetic User')
        self.assertEqual(body['school_ids'], ['2', '1'])
        self.assertEqual(body['permission_grants'][0]['school_id'], '2')

    def test_rejects_malformed_or_overreaching_payload_shapes(self):
        invalid = [
            {}, {'expected_revision': 1}, {'expected_revision': True, 'full_name': 'Name'},
            {'expected_revision': 0, 'full_name': 'Name'},
            {'expected_revision': 1, 'extra': 'field'},
            {'expected_revision': 1, 'full_name': '  '},
            {'expected_revision': 1, 'role': 'owner'},
            {'expected_revision': 1, 'account_status': 'deleted'},
            {'expected_revision': 1, 'school_ids': ['01']},
            {'expected_revision': 1, 'school_ids': ['1', '1']},
            {'expected_revision': 1, 'permission_grants': [
                {'permission_key': 'audit.read', 'school_id': '3'}]},
            {'expected_revision': 1, 'permission_grants': [
                {'permission_key': 'unknown', 'school_id': None}]},
            {'expected_revision': 1, 'permission_grants': [
                {'permission_key': ['audit.read'], 'school_id': None}]},
            {'expected_revision': 1, 'role': ['admin']},
            {'expected_revision': 1, 'account_status': ['disabled']},
        ]
        for body in invalid:
            with self.subTest(body=body), self.assertRaises(ApiError):
                validate_account_update(body)

    def test_update_route_and_sql_projection(self):
        response = self.client.patch('/api/v1/accounts/' + TARGET,
            json={'expected_revision': 2, 'full_name': 'Synthetic account'}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['data']['user_id'], TARGET)
        sql, params = self.repo.execute.call_args.args
        self.assertIn('graphiscan_update_account', sql)
        self.assertEqual(params[0:3], (ACTOR, SESSION, TARGET))
        self.assertEqual(json.loads(params[3]), {'expected_revision': 2, 'full_name': 'Synthetic account'})
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_server_guard_and_fail_closed_writer_setup(self):
        self.assertEqual(self.client.patch('/api/v1/accounts/' + TARGET, json={}).status_code, 401)
        original = self.state
        self.state = replace(original, grants=(Grant('accounts.manage', '9'),))
        denied = self.client.patch('/api/v1/accounts/' + TARGET,
            json={'expected_revision': 2, 'full_name': 'Name'}, headers=self.headers)
        self.assertEqual(denied.status_code, 403)
        self.repo.execute.assert_not_called()

    def test_database_and_writer_errors_are_sanitized(self):
        self.repo.execute.side_effect = RuntimeError('private DSN text')
        response = self.client.patch('/api/v1/accounts/' + TARGET,
            json={'expected_revision': 2, 'full_name': 'Name'}, headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private DSN', response.text)
        self.repo.execute.side_effect = None
        self.repo.execute.return_value = {'result': {'code': 'LAST_ADMIN'}}
        response = self.client.patch('/api/v1/accounts/' + TARGET,
            json={'expected_revision': 2, 'account_status': 'disabled'}, headers=self.headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json['error']['code'], 'LAST_ADMIN')


if __name__ == '__main__':
    unittest.main()
