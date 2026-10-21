"""Bounded school/student reads; SQL repeats current session, gates and scope.

Cursors are signed, short-lived and bound to the actor, session and filters.
The random process key deliberately invalidates cursors on API restart.
"""
import base64
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from datetime import datetime
from uuid import UUID

from api_v1 import ApiError, BackendUnavailable


def invalid_query():
    return ApiError(422, 'INVALID_QUERY', 'Check the list filters or start a new list.')


def record_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]{0,18}', value) or int(value) > 9223372036854775807:
        raise invalid_query()
    return value


class DirectoryService:
    def __init__(self, connect, *, cursor_key=None, now=None):
        self.connect = connect
        self.key = cursor_key if cursor_key is not None else secrets.token_bytes(32)
        self.now = now if now is not None else time.time

    def read(self, identity, resource, args, target=None):
        allowed = {'limit', 'cursor', 'q'}
        if resource == 'students':
            allowed |= {'school_id', 'grade_level'}
        if resource == 'student':
            allowed = set()
            record_id(target)
        if any(key not in allowed or len(args.getlist(key)) != 1 for key in args):
            raise invalid_query()
        limit = args.get('limit', '25')
        if not re.fullmatch(r'[1-9][0-9]{0,2}', limit) or int(limit) > 100:
            raise invalid_query()
        limit = int(limit)
        search = args.get('q', '').strip()
        if len(search) > 120 or any(ord(c) < 32 for c in search):
            raise invalid_query()
        school = args.get('school_id')
        if school is not None:
            record_id(school)
        grade = args.get('grade_level')
        if grade is not None and grade not in ('1', '2', '3'):
            raise invalid_query()
        binding = [identity.user_id, identity.session_id, resource, search, school, grade, limit]
        after_time, after_id = None, None
        if 'cursor' in args:
            after_time, after_id = self.decode_cursor(args['cursor'], binding)
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute('''SELECT public.graphiscan_read_directory(
                        %s::uuid,%s::uuid,%s::text,%s::text,%s::bigint,%s::smallint,
                        %s::timestamptz,%s::bigint,%s::integer,%s::bigint) AS result''',
                        (identity.user_id, identity.session_id, resource, search, school,
                         grade, after_time, after_id, limit, target))
                    result = cursor.fetchone()['result']
            if not isinstance(result, dict) or not isinstance(result.get('rows'), list):
                raise BackendUnavailable()
        except Exception as error:
            state=getattr(error,'sqlstate',None)
            safe_state=state if isinstance(state,str) and re.fullmatch(r'[A-Z0-9]{5}',state) else 'UNCLASSIFIED'
            logging.getLogger(__name__).warning('Directory read unavailable; SQLSTATE=%s',safe_state)
            raise BackendUnavailable() from None
        errors = {
            'AUTHENTICATION_REQUIRED': (401, 'Sign in to continue.', None),
            'ACCOUNT_UNAVAILABLE': (403, 'This account is unavailable.', None),
            'PASSWORD_CHANGE_REQUIRED': (403, 'Change your password to continue.', 'change_password'),
            'AGREEMENT_NOT_CONFIGURED': (503, 'The privacy agreement is unavailable.', 'agreement_unavailable'),
            'PRIVACY_ACCEPTANCE_REQUIRED': (403, 'Read and accept the current privacy agreement to continue.', 'accept_privacy'),
            'FORBIDDEN': (403, 'You do not have access to this feature.', None),
            'INVALID_QUERY': (422, 'Check the list filters or start a new list.', None),
        }
        code = result.get('code')
        if code is not None:
            if code not in errors:
                raise BackendUnavailable()
            status, message, action = errors[code]
            raise ApiError(status, code, message, action)
        rows = result['rows']
        if resource == 'student':
            if not rows:
                raise ApiError(404, 'NOT_FOUND', 'The requested record was not found.')
            return {'data': rows[0]}
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = self.encode_cursor(binding, last['created_at'], last['school_id' if resource == 'schools' else 'student_id'])
        return {'data': rows, 'page': {'next_cursor': next_cursor}}

    def encode_cursor(self, binding, created_at, last_id):
        body = json.dumps([binding, created_at, last_id, int(self.now()) + 1800], separators=(',', ':')).encode()
        signature = hmac.digest(self.key, body, hashlib.sha256)
        return base64.urlsafe_b64encode(body + signature).decode().rstrip('=')

    def decode_cursor(self, token, binding, *, uuid_key=False):
        try:
            if not token or len(token) > 2048 or not re.fullmatch(r'[A-Za-z0-9_-]+', token):
                raise ValueError()
            raw = base64.b64decode(token + '=' * (-len(token) % 4), altchars=b'-_', validate=True)
            body, signature = raw[:-32], raw[-32:]
            if not hmac.compare_digest(hmac.digest(self.key, body, hashlib.sha256), signature):
                raise ValueError()
            scope, timestamp, last_id, expiry = json.loads(body)
            if scope != binding or type(expiry) is not int or expiry <= self.now():
                raise ValueError()
            parsed = datetime.fromisoformat(timestamp)
            if parsed.tzinfo is None:
                raise ValueError()
            if uuid_key:
                if str(UUID(last_id)) != last_id:
                    raise ValueError()
            else:
                record_id(last_id)
            return timestamp, last_id
        except Exception:
            raise invalid_query() from None
