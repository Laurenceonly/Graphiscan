"""Account administration writes with database-side authorization and revisions."""
import json
import re
from uuid import UUID

from api_v1 import ApiError, BackendUnavailable

ROLES = {'admin', 'researcher', 'teacher', 'parent', 'expert', 'guest'}
STATUSES = {'active', 'pending', 'disabled', 'rejected'}
PERMISSIONS = {'accounts.manage', 'permissions.manage', 'schools.manage',
               'assignments.manage', 'audit.read'}
ERRORS = {
    'INVALID_ACCOUNT_ID': (422, 'Supply a valid account ID.', None),
    'AUTHENTICATION_REQUIRED': (401, 'Sign in to continue.', None),
    'ACCOUNT_UNAVAILABLE': (403, 'This account is unavailable.', None),
    'PASSWORD_CHANGE_REQUIRED': (403, 'Change your password to continue.', 'change_password'),
    'AGREEMENT_NOT_CONFIGURED': (503, 'The privacy agreement is unavailable.', 'agreement_unavailable'),
    'PRIVACY_ACCEPTANCE_REQUIRED': (403, 'Read and accept the current privacy agreement to continue.', 'accept_privacy'),
    'FORBIDDEN': (403, 'You do not have access to this operation.', None),
    'NOT_FOUND': (404, 'The requested account was not found.', None),
    'REVISION_CONFLICT': (409, 'This account changed. Reload it before saving again.', None),
    'LAST_ADMIN': (409, 'The last active administrator cannot be disabled or demoted.', None),
    'INVALID_INPUT': (422, 'Check the supplied account fields.', None),
    'INVALID_ASSIGNMENT': (422, 'Choose schools or permission scopes available to your account.', None),
}


def _invalid():
    return ApiError(422, 'INVALID_INPUT', 'Check the supplied account fields.')


def _school_ids(value):
    if not isinstance(value, list) or len(value) > 128:
        raise _invalid()
    output = []
    for item in value:
        if not isinstance(item, str) or not re.fullmatch(r'[1-9][0-9]{0,18}', item):
            raise _invalid()
        if int(item) > 9223372036854775807 or item in output:
            raise _invalid()
        output.append(item)
    return output


def _permission_grants(value):
    if not isinstance(value, list) or len(value) > 128:
        raise _invalid()
    output, seen = [], set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {'permission_key', 'school_id'}:
            raise _invalid()
        key, school = item['permission_key'], item['school_id']
        if not isinstance(key, str) or key not in PERMISSIONS:
            raise _invalid()
        if school is not None:
            if not isinstance(school, str) or not re.fullmatch(r'[1-9][0-9]{0,18}', school):
                raise _invalid()
            if int(school) > 9223372036854775807:
                raise _invalid()
        if key in {'accounts.manage', 'permissions.manage', 'audit.read'} and school is not None:
            raise _invalid()
        pair = (key, school)
        if pair in seen:
            raise _invalid()
        seen.add(pair)
        output.append({'permission_key': key, 'school_id': school})
    return output


def validate_account_update(body):
    allowed = {'expected_revision', 'full_name', 'role', 'account_status',
               'school_ids', 'permission_grants'}
    if (not isinstance(body, dict) or set(body) - allowed or
            'expected_revision' not in body or len(body) < 2):
        raise _invalid()
    body = dict(body)
    revision = body['expected_revision']
    if type(revision) is not int or not 1 <= revision <= 9223372036854775806:
        raise _invalid()
    if 'full_name' in body:
        name = body['full_name']
        if not isinstance(name, str) or any(ord(char) < 32 or ord(char) == 127 for char in name):
            raise _invalid()
        name = ' '.join(name.split())
        if not 1 <= len(name) <= 200:
            raise _invalid()
        body['full_name'] = name
    if 'role' in body and (not isinstance(body['role'], str) or body['role'] not in ROLES):
        raise _invalid()
    if 'account_status' in body and (not isinstance(body['account_status'], str) or body['account_status'] not in STATUSES):
        raise _invalid()
    if 'school_ids' in body:
        body['school_ids'] = _school_ids(body['school_ids'])
    if 'permission_grants' in body:
        body['permission_grants'] = _permission_grants(body['permission_grants'])
    return body


def _target_uuid(value):
    try:
        if (not isinstance(value, str) or
                not re.fullmatch(r'[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', value)):
            raise ValueError()
        return str(UUID(value))
    except (ValueError, TypeError):
        raise ApiError(422, 'INVALID_ACCOUNT_ID', 'Supply a valid account ID.') from None


class AdminWriteService:
    def __init__(self, repository):
        self.repository = repository

    def update(self, identity, target, body, request_id):
        target = _target_uuid(target)
        body = validate_account_update(body)
        try:
            UUID(request_id)
        except (TypeError, ValueError):
            raise BackendUnavailable() from None
        if self.repository is None:
            raise BackendUnavailable()
        try:
            row = self.repository.execute(
                'SELECT public.graphiscan_update_account(%s::uuid,%s::uuid,%s::uuid,%s::jsonb,%s::uuid) AS result',
                (identity.user_id, identity.session_id, target,
                 json.dumps(body, separators=(',', ':'), ensure_ascii=False), request_id))
        except Exception:
            raise BackendUnavailable() from None
        result = row.get('result') if isinstance(row, dict) else None
        if not isinstance(result, dict) or 'code' not in result:
            raise BackendUnavailable()
        code = result['code']
        if code is not None:
            if code not in ERRORS:
                raise BackendUnavailable()
            status, message, action = ERRORS[code]
            raise ApiError(status, code, message, action)
        data = result.get('data')
        if not isinstance(data, dict) or data.get('user_id') != target:
            raise BackendUnavailable()
        return {'data': data}


class PostgresAdminWriteRepository:
    """Dedicated account writer connection; never reuse the read-only reader."""
    def __init__(self, connect):
        self.connect = connect

    def execute(self, sql, params):
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    row = cursor.fetchone()
            return row
        except Exception:
            raise BackendUnavailable() from None
