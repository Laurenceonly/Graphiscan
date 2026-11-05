"""Role-based school/grade eligibility and explicit parent/student links."""
from uuid import UUID
import json

from api_v1 import ApiError, BackendUnavailable
from v1_admin_writes import _target_uuid, _school_ids
from v1_account_issuance import _result
from v1_directory import record_id


def validate_role_assignments(body):
    def invalid():
        return ApiError(422, 'INVALID_INPUT', 'Choose valid schools, grades and students.')
    if not isinstance(body, dict) or set(body) not in (
            {'expected_revision', 'school_grades'}, {'expected_revision', 'student_links'}):
        raise invalid()
    revision = body['expected_revision']
    if type(revision) is not int or not 1 <= revision <= 9223372036854775806:
        raise invalid()
    result = {'expected_revision': revision}
    if 'school_grades' in body:
        scopes = body['school_grades']
        if not isinstance(scopes, list) or len(scopes) > 384:
            raise invalid()
        seen = set()
        for scope in scopes:
            if not isinstance(scope, dict) or set(scope) != {'school_id', 'grade_level'}:
                raise invalid()
            _school_ids([scope['school_id']])
            grade = scope['grade_level']
            pair = (scope['school_id'], grade)
            if type(grade) is not int or grade not in (1, 2, 3) or pair in seen:
                raise invalid()
            seen.add(pair)
        result['school_grades'] = scopes
    else:
        links = body['student_links']
        if not isinstance(links, list) or not 1 <= len(links) <= 128:
            raise invalid()
        seen = set()
        for link in links:
            if not isinstance(link, dict) or set(link) != {'student_id', 'expected_revision', 'linked'}:
                raise invalid()
            record_id(link['student_id'])
            rev = link['expected_revision']
            if (type(rev) is not int or not 1 <= rev <= 9223372036854775806
                    or type(link['linked']) is not bool or link['student_id'] in seen):
                raise invalid()
            seen.add(link['student_id'])
        result['student_links'] = links
    return result


class RoleAssignmentsService:
    def __init__(self, reader, writer=None):
        self.reader, self.writer = reader, writer

    def read(self, identity, target):
        target = _target_uuid(target)
        return self._run(self.reader,
            'SELECT public.graphiscan_get_role_assignments(%s::uuid,%s::uuid,%s::uuid) AS result',
            (identity.user_id, identity.session_id, target), target)

    def write(self, identity, target, body, request_id):
        target, body = _target_uuid(target), validate_role_assignments(body)
        try:
            UUID(request_id)
        except (ValueError, TypeError):
            raise BackendUnavailable() from None
        return self._run(self.writer,
            'SELECT public.graphiscan_set_role_assignments(%s::uuid,%s::uuid,%s::uuid,%s::jsonb,%s::uuid) AS result',
            (identity.user_id, identity.session_id, target, json.dumps(body), request_id), target)

    @staticmethod
    def _run(repository, sql, params, target):
        if repository is None:
            raise BackendUnavailable()
        try:
            row = repository.execute(sql, params)
        except Exception:
            raise BackendUnavailable() from None
        result = _result(row)
        data = result.get('data')
        if (not isinstance(data, dict) or data.get('user_id') != target
                or data.get('role') not in ('teacher', 'expert', 'parent')
                or type(data.get('revision')) is not int
                or not isinstance(data.get('school_grades'), list)
                or not isinstance(data.get('students'), list)):
            raise BackendUnavailable()
        return {'data': data}
