"""Explicit scoped eligibility API boundaries; mocked DB only."""
import unittest
from dataclasses import replace
from unittest.mock import Mock
from uuid import UUID

from flask import Flask

from api_v1 import AccessState, Grant, Identity, install_api_v1
from v1_assignment_access import AssignmentAccessService

A = '00000000-0000-4000-8000-000000000001'
S = '00000000-0000-4000-8000-000000000002'
C = '00000000-0000-4000-8000-000000000003'
T = '00000000-0000-4000-8000-000000000004'


class AssignmentAccessTests(unittest.TestCase):
    def setUp(self):
        self.reader, self.writer = Mock(), Mock()
        self.data = {'candidate_id': C, 'actor_id': T, 'school_id': '9', 'revision': 3,
                     'candidate_role': 'parent', 'eligible': True, 'effective': True, 'can_grant': True}
        for repo in (self.reader, self.writer):
            repo.execute.return_value = {'result': {'code': None, 'data': self.data}}
        self.service = AssignmentAccessService(self.reader, self.writer)
        self.state = AccessState(A, 'Fictional admin', 'admin', 'active', False,
            'fixture', 'fixture', grants=(Grant('accounts.manage'),))
        self.backend = Mock()
        self.backend.authenticate.return_value = Identity(A, S)
        self.backend.load_access.side_effect = lambda identity: self.state
        self.backend.assignment_access_service = self.service
        app = Flask(__name__)
        install_api_v1(app, self.backend)
        self.client = app.test_client()
        self.path = '/api/v1/accounts/' + C + '/assignment-access'
        self.headers = {'Authorization': 'Bearer fictional'}
        self.body = {'actor_id': T, 'school_id': '9', 'expected_revision': 2, 'eligible': True}

    def get(self, query=None):
        return self.client.get(self.path, query_string=query or {'actor_id': T, 'school_id': '9'}, headers=self.headers)

    def patch(self, body=None):
        return self.client.patch(self.path, json=self.body if body is None else body, headers=self.headers)

    def test_read_uses_reader_with_explicit_identity_pair_and_school(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['data'], self.data)
        self.assertEqual(self.reader.execute.call_args.args[1], (A, S, C, T, '9'))
        self.writer.execute.assert_not_called()
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_write_uses_dedicated_writer_and_server_request_id(self):
        response = self.patch()
        self.assertEqual(response.status_code, 200)
        sql, params = self.writer.execute.call_args.args
        self.assertIn('graphiscan_set_assignment_access', sql)
        self.assertEqual(params[:7], (A, S, C, T, '9', 2, True))
        self.assertEqual(str(UUID(params[7])), response.json['request_id'])
        self.reader.execute.assert_not_called()

    def test_missing_or_scoped_account_grant_and_teacher_role_deny_before_database(self):
        self.assertEqual(self.client.get(self.path).status_code, 401)
        self.state = replace(self.state, grants=(Grant('accounts.manage', '9'),))
        self.assertEqual(self.get().status_code, 403)
        self.state = replace(self.state, role='teacher', grants=(Grant('accounts.manage'),))
        self.assertEqual(self.patch().status_code, 403)
        self.reader.execute.assert_not_called()
        self.writer.execute.assert_not_called()

    def test_sql_scope_denial_is_enforced_despite_global_account_grant(self):
        self.writer.execute.return_value = {'result': {'code': 'FORBIDDEN'}}
        self.assertEqual(self.patch().status_code, 403)

    def test_invalid_or_duplicate_fields_never_reach_database(self):
        for body in ({**self.body, 'eligible': 'true'}, {**self.body, 'expected_revision': True},
                     {**self.body, 'school_id': '09'}, {**self.body, 'actor_id': 'invalid'},
                     {**self.body, 'extra': 'value'}):
            with self.subTest(body=body):
                self.assertEqual(self.patch(body).status_code, 422)
        self.assertEqual(self.get([('actor_id', T), ('actor_id', A), ('school_id', '9')]).status_code, 422)
        self.assertEqual(self.get({'actor_id': T, 'school_id': '9', 'extra': 'value'}).status_code, 422)
        self.reader.execute.assert_not_called()
        self.writer.execute.assert_not_called()

    def test_missing_writer_does_not_fall_back_to_reader(self):
        self.service.writer = None
        self.assertEqual(self.get().status_code, 200)
        self.reader.execute.reset_mock()
        self.assertEqual(self.patch().status_code, 503)
        self.reader.execute.assert_not_called()

    def test_stale_revision_and_missing_prerequisites_are_recoverable_errors(self):
        self.writer.execute.return_value = {'result': {'code': 'REVISION_CONFLICT'}}
        self.assertEqual(self.patch().status_code, 409)
        self.writer.execute.return_value = {'result': {'code': 'INVALID_ASSIGNMENT'}}
        response = self.patch()
        self.assertEqual(response.status_code, 422)
        self.assertIn('school access', response.json['error']['message'])

    def test_database_failure_and_incorrect_projection_fail_closed(self):
        self.writer.execute.side_effect = RuntimeError('private database text')
        response = self.patch()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private database text', response.text)
        self.reader.execute.return_value = {'result': {'code': None, 'data': {**self.data, 'actor_id': A}}}
        self.assertEqual(self.get().status_code, 503)


if __name__ == '__main__':
    unittest.main()
