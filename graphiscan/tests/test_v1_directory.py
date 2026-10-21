"""Directory HTTP/service boundaries; record authorization is tested in SQL."""
import unittest
from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import Mock

from flask import Flask
from werkzeug.datastructures import MultiDict

from api_v1 import AccessState, Identity, install_api_v1
from v1_directory import DirectoryService

USER = '00000000-0000-4000-8000-000000000001'
SESSION = '00000000-0000-4000-8000-000000000002'
STAMP = '2026-10-20T00:00:00+00:00'


class DirectoryTests(unittest.TestCase):
    def setUp(self):
        self.identity = Identity(USER, SESSION)
        self.state = AccessState(USER, 'Fictional teacher', 'teacher', 'active', False, 'test', 'test')
        self.result = {'code': None, 'rows': []}
        self.executions = []
        self.failure = False

        @contextmanager
        def connect():
            if self.failure:
                raise RuntimeError('private DSN SQL token')
            cursor = Mock()
            cursor.execute.side_effect = lambda *args: self.executions.append(args)
            cursor.fetchone.side_effect = lambda: {'result': self.result}
            connection = Mock()
            connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
            connection.cursor.return_value.__exit__ = Mock(return_value=False)
            yield connection

        self.clock = 1000
        self.service = DirectoryService(connect, cursor_key=b'x' * 32, now=lambda: self.clock)
        self.backend = Mock()
        self.backend.authenticate.return_value = self.identity
        self.backend.load_access.side_effect = lambda identity: self.state
        self.backend.directory_service = self.service
        app = Flask(__name__)
        install_api_v1(app, self.backend)
        self.client = app.test_client()
        self.headers = {'Authorization': 'Bearer fictional'}

    def get(self, path='/students'):
        return self.client.get('/api/v1' + path, headers=self.headers)

    def test_empty_scoped_list_and_no_store(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['data'], [])
        self.assertEqual(response.json['page'], {'next_cursor': None})
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_unauthed_and_onboarding_never_query_records(self):
        self.assertEqual(self.client.get('/api/v1/students').status_code, 401)
        for changes, code in [({'must_change_password': True}, 'PASSWORD_CHANGE_REQUIRED'),
                              ({'accepted_agreement_version': None}, 'PRIVACY_ACCEPTANCE_REQUIRED'),
                              ({'account_status': 'disabled'}, 'ACCOUNT_UNAVAILABLE'),
                              ({'role': 'guest'}, 'FORBIDDEN')]:
            self.state = replace(self.state, **changes)
            self.assertEqual(self.get().json['error']['code'], code)
            self.state = AccessState(USER, 'Fictional', 'teacher', 'active', False, 'test', 'test')
        self.assertEqual(self.executions, [])

    def test_unknown_duplicate_and_invalid_filters_rejected_before_sql(self):
        for query in ['teacher_id=anything', 'q=a&q=b', 'limit=0', 'limit=101', 'limit=-1',
                      'limit=01', 'grade_level=4', 'grade_level=1.0', 'school_id=0',
                      'school_id=9223372036854775808', 'school_id=01', 'q=' + 'a' * 121,
                      'q=a%00b', 'cursor=', 'cursor=invalid']:
            with self.subTest(query=query):
                self.assertEqual(self.get('/students?' + query).status_code, 422)
        self.assertEqual(self.get('/schools?grade_level=1').status_code, 422)
        self.assertEqual(self.executions, [])

    def test_bigint_bounds_and_detail_filters(self):
        for target in ['0', '-1', '01', 'abc', '9223372036854775808']:
            self.assertEqual(self.get('/students/' + target).status_code, 422)
        self.assertEqual(self.get('/students/1?q=other').status_code, 422)
        self.assertEqual(self.get('/students/9223372036854775807').status_code, 404)

    def test_search_is_bound_value_with_literal_wildcards(self):
        self.assertEqual(self.get('/students?q=%25_%27&school_id=9&grade_level=2').status_code, 200)
        sql, parameters = self.executions[-1]
        self.assertNotIn("%_'", sql)
        self.assertEqual(parameters[:6], (USER, SESSION, 'students', "%_'", '9', '2'))

    def test_detail_missing_and_authorized_projection(self):
        self.assertEqual(self.get('/students/9').status_code, 404)
        self.result['rows'] = [{'student_id': '9', 'created_at': STAMP}]
        self.assertEqual(self.get('/students/9').json['data']['student_id'], '9')
        self.assertNotIn('page', self.get('/students/9').json)

    def test_database_gate_change_after_http_guard_is_respected(self):
        for code, status in [('AUTHENTICATION_REQUIRED', 401), ('ACCOUNT_UNAVAILABLE', 403),
                             ('PASSWORD_CHANGE_REQUIRED', 403), ('AGREEMENT_NOT_CONFIGURED', 503),
                             ('PRIVACY_ACCEPTANCE_REQUIRED', 403), ('FORBIDDEN', 403)]:
            self.result = {'code': code, 'rows': []}
            response = self.get()
            self.assertEqual(response.status_code, status)
            self.assertEqual(response.json['error']['code'], code)

    def test_service_and_unknown_database_failures_are_sanitized(self):
        self.failure = True
        response = self.get()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private', response.text)
        self.failure = False
        for result in [None, {'code': None, 'rows': None}, {'code': 'private SQL', 'rows': []}]:
            self.result = result
            response = self.get()
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private', response.text)

    def test_cursor_keyset_has_no_duplicate_boundary_and_large_ids_stay_strings(self):
        self.result['rows'] = [{'student_id': '9223372036854775807', 'created_at': STAMP},
                               {'student_id': '3', 'created_at': STAMP}]
        response = self.get('/students?limit=1')
        cursor = response.json['page']['next_cursor']
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(response.json['data'][0]['student_id'], '9223372036854775807')
        self.result['rows'] = []
        self.assertEqual(self.get('/students?limit=1&cursor=' + cursor).status_code, 200)
        self.assertEqual(self.executions[-1][1][6:8], (STAMP, '9223372036854775807'))

    def test_cursor_tamper_actor_session_filters_resource_limit_and_expiry(self):
        binding = [USER, SESSION, 'students', '', None, None, 25]
        token = self.service.encode_cursor(binding, STAMP, '1')
        self.assertEqual(self.get('/students?cursor=' + token).status_code, 200)
        for path in ['/schools?cursor=', '/students?q=changed&cursor=', '/students?limit=1&cursor=']:
            self.assertEqual(self.get(path + token).status_code, 422)
        self.assertEqual(self.get('/students?cursor=' + token[:-5] + 'AAAAA').status_code, 422)
        for changed in [Identity(SESSION, SESSION), Identity(USER, USER)]:
            self.backend.authenticate.return_value = changed
            self.state = replace(self.state, user_id=changed.user_id)
            self.assertEqual(self.get('/students?cursor=' + token).status_code, 422)
        self.backend.authenticate.return_value = self.identity
        self.state = replace(self.state, user_id=USER)
        self.clock = 2800
        self.assertEqual(self.get('/students?cursor=' + token).status_code, 422)

    def test_restarted_process_rejects_old_cursor(self):
        token = DirectoryService(None, cursor_key=b'y' * 32, now=lambda: 1000).encode_cursor(
            [USER, SESSION, 'students', '', None, None, 25], STAMP, '1')
        self.assertEqual(self.get('/students?cursor=' + token).status_code, 422)


if __name__ == '__main__':
    unittest.main()
