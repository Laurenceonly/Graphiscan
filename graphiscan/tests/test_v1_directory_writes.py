"""Synthetic HTTP/write-service checks; transactional rules execute in SQL tests."""
import json
import unittest
from dataclasses import replace
from unittest.mock import Mock

from flask import Flask

from api_v1 import AccessState, BackendUnavailable, Identity, install_api_v1
from v1_directory_writes import DirectoryWriteService

USER = '00000000-0000-4000-8000-000000000001'
SESSION = '00000000-0000-4000-8000-000000000002'
KEY = 'fictional_creation_key_01'


class DirectoryWriteTests(unittest.TestCase):
    def setUp(self):
        self.backend = Mock()
        self.backend.authenticate.return_value = Identity(USER, SESSION)
        self.state = AccessState(USER, 'Fictional', 'admin', 'active', False, 'v1', 'v1')
        self.backend.load_access.side_effect = lambda identity: self.state
        self.repository = Mock()
        self.repository.execute.return_value = {'result': {'code': None,
            'data': {'school_id': '9', 'student_id': '10'}, 'warnings': []}}
        self.backend.directory_write_service = DirectoryWriteService(self.repository)
        app = Flask(__name__)
        install_api_v1(app, self.backend)
        self.client = app.test_client()
        self.headers = {'Authorization': 'Bearer fictional', 'Idempotency-Key': KEY}
        self.student = {'full_name': 'Fictional Child', 'age': 8, 'school_id': '9', 'grade_level': 1}

    def send(self, path='/students', body=None, method='POST', headers=None):
        return self.client.open('/api/v1' + path, method=method,
            json=self.student if body is None else body, headers=self.headers if headers is None else headers)

    def test_create_and_update_status_location_no_store_and_request_id(self):
        for path, body, method, status, location in [
            ('/students', self.student, 'POST', 201, '/api/v1/students/10'),
            ('/schools', {'name': 'Fictional School'}, 'POST', 201, '/api/v1/schools/9'),
            ('/students/10', {'age': 9, 'expected_revision': 1}, 'PATCH', 200, None),
            ('/schools/9', {'name': 'New Name', 'expected_revision': 1}, 'PATCH', 200, None)]:
            response = self.send(path, body, method)
            self.assertEqual(response.status_code, status)
            self.assertEqual(response.headers.get('Location'), location)
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertEqual(response.headers['X-Request-ID'], response.json['request_id'])

    def test_roles_onboarding_and_disabled_block_before_writer(self):
        for changes, code in [({'role': 'parent'}, 'FORBIDDEN'), ({'role': 'expert'}, 'FORBIDDEN'),
                              ({'role': 'guest'}, 'FORBIDDEN'), ({'must_change_password': True}, 'PASSWORD_CHANGE_REQUIRED'),
                              ({'accepted_agreement_version': None}, 'PRIVACY_ACCEPTANCE_REQUIRED'),
                              ({'account_status': 'disabled'}, 'ACCOUNT_UNAVAILABLE')]:
            original = self.state
            self.state = replace(original, **changes)
            self.assertEqual(self.send().json['error']['code'], code)
            self.state = original
        self.assertEqual(self.client.post('/api/v1/students', json=self.student).status_code, 401)
        self.repository.execute.assert_not_called()

    def test_teacher_can_enter_student_flow_but_not_school_flow(self):
        self.state = replace(self.state, role='teacher')
        self.assertEqual(self.send().status_code, 201)
        self.assertEqual(self.send('/schools', {'name': 'Fictional'}).status_code, 403)

    def test_strict_student_fields_and_bounds(self):
        for field, value in [('full_name', ''), ('full_name', 'x' * 201), ('full_name', 'bad\nname'),
                             ('age', True), ('age', 0), ('age', 32768), ('age', 8.0), ('age', None),
                             ('grade_level', 4), ('grade_level', '1'), ('school_id', 9),
                             ('school_id', '01'), ('school_id', '9223372036854775808'),
                             ('teacher_id', None), ('teacher_id', 'bad'), ('parent_id', 'bad'),
                             ('role', 'admin'), ('expected_revision', 1)]:
            with self.subTest(field=field, value=value):
                self.assertEqual(self.send(body={**self.student, field: value}).status_code, 422)
        self.repository.execute.assert_not_called()

    def test_revision_and_empty_patch_validation(self):
        for body in [{}, {'expected_revision': 1}, {'age': 9}, {'age': 9, 'expected_revision': True},
                     {'age': 9, 'expected_revision': 0}, {'age': 9, 'expected_revision': 9223372036854775808}]:
            self.assertEqual(self.send('/students/10', body, 'PATCH').status_code, 422)
        self.assertEqual(self.send('/students/01', {'age': 9, 'expected_revision': 1}, 'PATCH').status_code, 422)
        self.assertEqual(self.send('/schools', {'name': '   '}).status_code, 422)
        self.repository.execute.assert_not_called()

    def test_idempotency_key_required_and_bound_into_sql(self):
        for key in ['', 'short', 'x' * 129, 'contains spaces invalid']:
            response = self.send(headers={'Authorization': 'Bearer fictional', 'Idempotency-Key': key})
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json['error']['code'], 'IDEMPOTENCY_KEY_REQUIRED')
        self.repository.execute.assert_not_called()
        self.send()
        self.assertEqual(self.repository.execute.call_args.args[1][5], KEY)

    def test_normalization_uuid_and_null_parent_are_values_not_sql(self):
        response = self.send(body={**self.student, 'full_name': "  Fictional   O'Name  ",
                                   'teacher_id': USER.upper(), 'parent_id': None})
        self.assertEqual(response.status_code, 201)
        sql, args = self.repository.execute.call_args.args
        self.assertNotIn("O'Name", sql)
        payload = json.loads(args[4])
        self.assertEqual(payload['full_name'], "Fictional O'Name")
        self.assertEqual(payload['teacher_id'], USER)
        self.assertIsNone(payload['parent_id'])
        self.assertEqual(args[:3], (USER, SESSION, 'students.create'))

    def test_content_type_query_and_size_limits(self):
        self.assertEqual(self.client.post('/api/v1/students', data='x', headers=self.headers).status_code, 400)
        self.assertEqual(self.send('/students?role=admin').status_code, 400)
        self.assertEqual(self.send(body={'full_name': 'x' * 9000}).status_code, 413)
        self.assertEqual(self.client.post('/api/v1/students', json=[], headers=self.headers).status_code, 422)
        self.repository.execute.assert_not_called()

    def test_database_denials_and_conflicts_propagate_safely(self):
        for code, status in [('AUTHENTICATION_REQUIRED', 401), ('ACCOUNT_UNAVAILABLE', 403),
                             ('PASSWORD_CHANGE_REQUIRED', 403), ('AGREEMENT_NOT_CONFIGURED', 503),
                             ('PRIVACY_ACCEPTANCE_REQUIRED', 403), ('FORBIDDEN', 403),
                             ('NOT_FOUND', 404), ('REVISION_CONFLICT', 409),
                             ('IDEMPOTENCY_CONFLICT', 409), ('INVALID_ASSIGNMENT', 422)]:
            self.repository.execute.return_value = {'result': {'code': code}}
            response = self.send()
            self.assertEqual(response.status_code, status)
            self.assertEqual(response.json['error']['code'], code)
        self.repository.execute.return_value = {'result': {'code': 'private SQL text'}}
        response = self.send()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private', response.text)

    def test_duplicate_warning_and_fail_closed_writer_configuration(self):
        self.repository.execute.return_value['result']['warnings'] = ['duplicate_name']
        self.assertEqual(self.send().json['warnings'], ['duplicate_name'])
        self.backend.directory_write_service = DirectoryWriteService(None)
        self.assertEqual(self.send().status_code, 503)
        self.backend.directory_write_service = DirectoryWriteService(self.repository)
        self.repository.execute.side_effect = BackendUnavailable('private DSN')
        response = self.send()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private', response.text)

    def test_actual_app_preflight_allows_retry_header_and_patch(self):
        from app import app
        with app.test_client() as client:
            for method in ('POST', 'PATCH'):
                response = client.options('/api/v1/students' + ('/10' if method == 'PATCH' else ''),
                    headers={'Origin': 'http://127.0.0.1:5173',
                             'Access-Control-Request-Method': method,
                             'Access-Control-Request-Headers': 'Authorization,Content-Type,Idempotency-Key'})
                self.assertEqual(response.status_code, 200)
                self.assertIn('idempotency-key', response.headers['Access-Control-Allow-Headers'].lower())
                self.assertIn(method, response.headers['Access-Control-Allow-Methods'])


if __name__ == '__main__':
    unittest.main()
