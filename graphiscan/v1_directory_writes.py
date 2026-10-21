"""Strict input/projection boundary for transactional directory mutations."""
import json
import re
from uuid import UUID

from api_v1 import ApiError, BackendUnavailable
from v1_directory import record_id


def invalid_input():
    return ApiError(422, 'INVALID_INPUT', 'Check the supplied school or student fields.')


def validate_mutation(operation, body, key=None):
    if not isinstance(body, dict):
        raise invalid_input()
    creating = operation.endswith('.create')
    school = operation.startswith('schools.')
    allowed = {'name'} if school else {'full_name', 'age', 'school_id', 'grade_level', 'teacher_id', 'parent_id'}
    required = {'name'} if school else {'full_name', 'age', 'school_id', 'grade_level'} if creating else set()
    if not creating:
        allowed |= {'expected_revision'}
        required |= {'expected_revision'}
    if set(body) - allowed or not required <= set(body) or (not creating and len(body) < 2):
        raise invalid_input()
    body = dict(body)
    for field in ('name', 'full_name'):
        if field in body:
            value = body[field]
            if not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
                raise invalid_input()
            value = ' '.join(value.split())
            if not 1 <= len(value) <= 200:
                raise invalid_input()
            body[field] = value
    for field, maximum in [('age', 32767), ('grade_level', 3), ('expected_revision', 9223372036854775807)]:
        if field in body and (type(body[field]) is not int or not 1 <= body[field] <= maximum):
            raise invalid_input()
    if 'school_id' in body:
        try:
            record_id(body['school_id'])
        except ApiError:
            raise invalid_input() from None
    for field in ('teacher_id', 'parent_id'):
        if field in body:
            if field == 'parent_id' and body[field] is None:
                continue
            try:
                if not isinstance(body[field], str) or not re.fullmatch(r'[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', body[field]):
                    raise ValueError()
                body[field] = str(UUID(body[field]))
            except (ValueError, TypeError):
                raise invalid_input() from None
    if operation == 'students.create' and (not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,128}', key)):
        raise ApiError(422, 'IDEMPOTENCY_KEY_REQUIRED', 'Provide a valid Idempotency-Key and reuse it when retrying this creation.')
    return body


class DirectoryWriteService:
    def __init__(self, repository):
        self.repository = repository

    def write(self, identity, operation, target, body, key, request_id):
        body = validate_mutation(operation, body, key)
        if target is not None:
            record_id(target)
        if self.repository is None:
            raise BackendUnavailable()
        row = self.repository.execute('''SELECT public.graphiscan_write_directory(
            %s::uuid,%s::uuid,%s::text,%s::bigint,%s::jsonb,%s::text,%s::uuid) AS result''',
            (identity.user_id, identity.session_id, operation, target,
             json.dumps(body, separators=(',', ':'), ensure_ascii=False), key, request_id))
        result = row.get('result') if isinstance(row, dict) else None
        if not isinstance(result, dict) or 'code' not in result:
            raise BackendUnavailable()
        code = result['code']
        errors = {
            'AUTHENTICATION_REQUIRED': (401, 'Sign in to continue.', None),
            'ACCOUNT_UNAVAILABLE': (403, 'This account is unavailable.', None),
            'PASSWORD_CHANGE_REQUIRED': (403, 'Change your password to continue.', 'change_password'),
            'AGREEMENT_NOT_CONFIGURED': (503, 'The privacy agreement is unavailable.', 'agreement_unavailable'),
            'PRIVACY_ACCEPTANCE_REQUIRED': (403, 'Read and accept the current privacy agreement to continue.', 'accept_privacy'),
            'FORBIDDEN': (403, 'You do not have access to this operation.', None),
            'NOT_FOUND': (404, 'The requested record was not found.', None),
            'REVISION_CONFLICT': (409, 'This record changed. Reload it before saving again.', None),
            'IDEMPOTENCY_CONFLICT': (409, 'This request key was already used. Keep the original payload when retrying.', None),
            'INVALID_ASSIGNMENT': (422, 'Choose an eligible active teacher or parent for the school.', None),
            'INVALID_INPUT': (422, 'Check the supplied school or student fields.', None),
        }
        if code is not None:
            if code not in errors:
                raise BackendUnavailable()
            status, message, action = errors[code]
            raise ApiError(status, code, message, action)
        if not isinstance(result.get('data'), dict) or result.get('warnings') not in ([], ['duplicate_name']):
            raise BackendUnavailable()
        return {'data': result['data'], 'warnings': result['warnings']}
