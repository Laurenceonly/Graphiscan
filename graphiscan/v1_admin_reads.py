"""Bounded hosted account and audit reads with current server and SQL authorization."""
import re

from api_v1 import ApiError, BackendUnavailable
from v1_directory import DirectoryService, invalid_query


class AdminReadService(DirectoryService):
    def read(self, identity, resource, args):
        if resource not in {'accounts', 'audit'}:
            raise invalid_query()
        allowed = {'limit', 'cursor', 'q', 'role'} | ({'account_status'} if resource == 'accounts' else set())
        if any(key not in allowed or len(args.getlist(key)) != 1 for key in args):
            raise invalid_query()
        limit = args.get('limit', '25')
        if not re.fullmatch(r'[1-9][0-9]{0,2}', limit) or int(limit) > 100:
            raise invalid_query()
        limit = int(limit)
        search = args.get('q', '').strip()
        if len(search) > 120 or any(ord(char) < 32 for char in search):
            raise invalid_query()
        role = args.get('role') or None
        status = args.get('account_status') or None
        if role is not None and role not in {'admin', 'researcher', 'teacher', 'parent', 'expert', 'guest'}:
            raise invalid_query()
        if status is not None and status not in {'active', 'pending', 'disabled', 'rejected'}:
            raise invalid_query()
        binding = [identity.user_id, identity.session_id, resource, search, role, status, limit]
        after_time, after_key = self.decode_cursor(args['cursor'], binding, uuid_key=resource == 'accounts') if 'cursor' in args else (None, None)
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute('''SELECT public.graphiscan_read_admin(
                        %s::uuid,%s::uuid,%s::text,%s::text,%s::text,%s::text,
                        %s::timestamptz,%s::uuid,%s::bigint,%s::integer) AS result''',
                        (identity.user_id, identity.session_id, resource, search, role, status,
                         after_time, after_key if resource == 'accounts' else None,
                         after_key if resource == 'audit' else None, limit))
                    result = cursor.fetchone()['result']
            if not isinstance(result, dict) or not isinstance(result.get('rows'), list):
                raise BackendUnavailable()
        except Exception:
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
            status_code, message, action = errors[code]
            raise ApiError(status_code, code, message, action)
        rows = result['rows']
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = self.encode_cursor(binding, last['created_at'], last['user_id' if resource == 'accounts' else 'log_id'])
        return {'data': rows, 'page': {'next_cursor': next_cursor}}
