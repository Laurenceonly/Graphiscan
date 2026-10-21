"""Synthetic hosted admin read boundaries; no provider or database connection."""
import unittest
from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import Mock

from flask import Flask

from api_v1 import AccessState, Grant, Identity, install_api_v1
from v1_admin_reads import AdminReadService


USER = '00000000-0000-4000-8000-000000000001'
SESSION = '00000000-0000-4000-8000-000000000002'
STAMP = '2026-10-21T00:00:00+00:00'


class AdminReadTests(unittest.TestCase):
    def setUp(self):
        self.identity = Identity(USER, SESSION)
        self.state = AccessState(USER, 'Fictional admin', 'admin', 'active', False, 'test', 'test',
                                 grants=(Grant('accounts.manage'), Grant('audit.read')))
        self.result = {'code': None, 'rows': []}
        self.executions = []
        self.failure = False

        @contextmanager
        def connect():
            if self.failure:
                raise RuntimeError('private connection detail')
            cursor = Mock()
            cursor.execute.side_effect = lambda *args: self.executions.append(args)
            cursor.fetchone.side_effect = lambda: {'result': self.result}
            connection = Mock()
            connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
            connection.cursor.return_value.__exit__ = Mock(return_value=False)
            yield connection

        self.service = AdminReadService(connect, cursor_key=b'x' * 32, now=lambda: 1000)
        self.backend = Mock()
        self.backend.authenticate.return_value = self.identity
        self.backend.load_access.side_effect = lambda identity: self.state
        self.backend.admin_read_service = self.service
        app = Flask(__name__)
        install_api_v1(app, self.backend)
        self.client = app.test_client()
        self.headers = {'Authorization': 'Bearer fictional'}

    def get(self, path='/accounts'):
        return self.client.get('/api/v1' + path, headers=self.headers)

    def test_empty_lists_and_no_store(self):
        for path in ['/accounts', '/audit-logs']:
            response = self.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['data'], [])
            self.assertEqual(response.json['page'], {'next_cursor': None})
            self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_server_guards_before_sql(self):
        self.assertEqual(self.client.get('/api/v1/accounts').status_code, 401)
        original = self.state
        for changes, code in [({'role': 'teacher'}, 'FORBIDDEN'),
                              ({'must_change_password': True}, 'PASSWORD_CHANGE_REQUIRED'),
                              ({'accepted_agreement_version': None}, 'PRIVACY_ACCEPTANCE_REQUIRED'),
                              ({'account_status': 'disabled'}, 'ACCOUNT_UNAVAILABLE'),
                              ({'grants': (Grant('accounts.manage', '9'), Grant('audit.read', '9'))}, 'FORBIDDEN')]:
            self.state = replace(original, **changes)
            self.assertEqual(self.get().json['error']['code'], code)
        self.assertEqual(self.executions, [])

    def test_permissions_are_separate(self):
        self.state = replace(self.state, grants=(Grant('accounts.manage'),))
        self.assertEqual(self.get('/accounts').status_code, 200)
        self.assertEqual(self.get('/audit-logs').json['error']['code'], 'FORBIDDEN')
        self.state = replace(self.state, grants=(Grant('audit.read'),))
        self.assertEqual(self.get('/audit-logs').status_code, 200)
        self.assertEqual(self.get('/accounts').json['error']['code'], 'FORBIDDEN')

    def test_filters_and_cursor_are_bounded(self):
        for query in ['limit=0', 'limit=101', 'limit=01', 'q=a&q=b', 'role=owner',
                      'status=unknown', 'q=' + 'a' * 121, 'cursor=bad', 'school_id=1']:
            with self.subTest(query=query):
                self.assertEqual(self.get('/accounts?' + query).status_code, 422)
        self.assertEqual(self.get('/audit-logs?account_status=active').status_code, 422)
        self.assertEqual(self.executions, [])
        self.assertEqual(self.get('/accounts?q=%25_%27&role=teacher&account_status=active').status_code, 200)
        sql, params = self.executions[-1]
        self.assertNotIn("%_'", sql)
        self.assertEqual(params[2:6], ('accounts', "%_'", 'teacher', 'active'))

    def test_database_rechecks_and_sanitizes_failures(self):
        for code, status in [('AUTHENTICATION_REQUIRED', 401), ('ACCOUNT_UNAVAILABLE', 403),
                             ('PASSWORD_CHANGE_REQUIRED', 403), ('AGREEMENT_NOT_CONFIGURED', 503),
                             ('PRIVACY_ACCEPTANCE_REQUIRED', 403), ('FORBIDDEN', 403), ('INVALID_QUERY', 422)]:
            self.result = {'code': code, 'rows': []}
            self.assertEqual(self.get().status_code, status)
        self.failure = True
        self.assertEqual(self.get().status_code, 503)
        self.assertNotIn('private', self.get().text)
        self.failure = False
        self.result = {'code': 'private SQL', 'rows': []}
        self.assertEqual(self.get().status_code, 503)

    def test_account_and_audit_cursor_bind_resource_filters_actor(self):
        account = {'user_id': '00000000-0000-4000-8000-000000000003', 'created_at': STAMP}
        self.result = {'code': None, 'rows': [account, dict(account, user_id='00000000-0000-4000-8000-000000000004')]}
        response = self.get('/accounts?limit=1')
        token = response.json['page']['next_cursor']
        self.result = {'code': None, 'rows': []}
        self.assertEqual(self.get('/accounts?limit=1&cursor=' + token).status_code, 200)
        self.assertEqual(self.executions[-1][1][6:9], (STAMP, account['user_id'], None))
        self.assertEqual(self.get('/audit-logs?limit=1&cursor=' + token).status_code, 422)
        self.assertEqual(self.get('/accounts?limit=1&role=teacher&cursor=' + token).status_code, 422)
        self.result = {'code': None, 'rows': [{'log_id': '7', 'created_at': STAMP}, {'log_id': '6', 'created_at': STAMP}]}
        token = self.get('/audit-logs?limit=1').json['page']['next_cursor']
        self.result = {'code': None, 'rows': []}
        self.assertEqual(self.get('/audit-logs?limit=1&cursor=' + token).status_code, 200)
        self.assertEqual(self.executions[-1][1][7:9], (None, '7'))


if __name__ == '__main__':
    unittest.main()
