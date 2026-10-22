"""Bounded account details and durable administrator credential operations."""
import logging
import re
from uuid import UUID

import requests

from api_v1 import ApiError, BackendUnavailable
from v1_account_issuance import _result
from v1_admin_writes import _target_uuid


def _pending():
    return ApiError(503, 'ACCOUNT_OPERATION_PENDING',
                    'This operation could not be confirmed. Check its status before trying again. Account access stays blocked until it is resolved.')


def _key(value):
    try:
        if not isinstance(value, str) or str(UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError):
        raise ApiError(422, 'IDEMPOTENCY_KEY_REQUIRED', 'Provide a valid operation request ID.') from None
    return value


def validate_action(action, body):
    extra = 'temporary_password' if action == 'reset_password' else 'confirmation'
    if (not isinstance(body, dict) or set(body) != {'expected_revision', 'current_password', extra}
            or type(body['expected_revision']) is not int
            or not 1 <= body['expected_revision'] <= 9223372036854775806
            or not isinstance(body['current_password'], str)
            or not 1 <= len(body['current_password']) <= 4096):
        raise ApiError(422, 'INVALID_INPUT', 'Provide the account revision and your current password.')
    if action == 'reset_password':
        password = body[extra]
        if (not isinstance(password, str) or not 8 <= len(password) <= 128 or
                not all(re.search(pattern, password) for pattern in (r'[A-Z]', r'[a-z]', r'[0-9]', r'[^A-Za-z0-9]'))):
            raise ApiError(422, 'INVALID_PASSWORD', 'Use 8–128 characters with uppercase, lowercase, a number and a symbol.')
    elif body['confirmation'] != 'DELETE':
        raise ApiError(422, 'INVALID_INPUT', 'Type DELETE to confirm account removal.')


class AdminLifecycleService:
    def __init__(self, reader, writer=None, provider=None, password_provider=None):
        self.reader, self.writer = reader, writer
        self.provider, self.password_provider = provider, password_provider

    def detail(self, identity, target):
        target = _target_uuid(target)
        result = _result(self.reader.execute(
            'SELECT public.graphiscan_get_admin_account(%s::uuid,%s::uuid,%s::uuid) AS result',
            (identity.user_id, identity.session_id, target)))
        if not isinstance(result.get('data'), dict) or result['data'].get('user_id') != target:
            raise BackendUnavailable()
        return {'data': result['data']}

    def status(self, identity, operation):
        result = _result(self.reader.execute(
            'SELECT public.graphiscan_read_admin_account_operation(%s::uuid,%s::uuid,%s::uuid) AS result',
            (identity.user_id, identity.session_id, _key(operation))))
        if not isinstance(result.get('data'), dict):
            raise BackendUnavailable()
        return {'data': result['data']}

    def perform(self, identity, bearer, target, action, body, key, request_id):
        target, key = _target_uuid(target), _key(key)
        if action not in {'reset_password', 'delete'}:
            raise ApiError(422, 'INVALID_INPUT', 'Choose a valid account operation.')
        validate_action(action, body)
        if self.writer is None or self.provider is None or self.password_provider is None:
            raise ApiError(503, 'ACCOUNT_ACTION_UNAVAILABLE', 'Account actions are not configured. Contact the system operator.')
        # Confirm the actor password before reserving/blocking the target account.
        self.password_provider.verify_current(identity, bearer, body['current_password'])
        result = _result(self.writer.execute(
            'SELECT public.graphiscan_begin_admin_account_operation(%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s,%s,%s::uuid) AS result',
            (identity.user_id, identity.session_id, key, target, action, body['expected_revision'], request_id)))
        if isinstance(result.get('data'), dict):
            return {'data': result['data']}
        if result.get('reserved') is not True:
            raise BackendUnavailable()
        try:
            self._provider_action(target, action, body)
            result = _result(self.writer.execute(
                'SELECT public.graphiscan_complete_admin_account_operation(%s::uuid,%s::uuid,%s::uuid,%s::uuid) AS result',
                (identity.user_id, identity.session_id, key, request_id)))
            if not isinstance(result.get('data'), dict) or result['data'].get('user_id') != target:
                raise _pending()
            return {'data': result['data']}
        except Exception:
            # The durable pending gate survives timeouts or process interruption.
            # Never clear it, retry a provider write or claim rollback automatically.
            raise _pending() from None

    def _provider_action(self, target, action, body):
        method = 'PUT' if action == 'reset_password' else 'DELETE'
        payload = {'password': body['temporary_password']} if action == 'reset_password' else {'should_soft_delete': False}
        try:
            response = self.provider.http.request(method, self.provider.origin + '/auth/v1/admin/users/' + target,
                headers={'apikey': self.provider.secret}, json=payload,
                timeout=(3.05, 8), allow_redirects=False)
        except requests.RequestException:
            raise _pending() from None
        try:
            if response.status_code not in (200, 204):
                logging.getLogger(__name__).error('auth_account_action_failed action=%s status=%s', action, response.status_code)
                raise _pending()
            if action == 'reset_password':
                user = response.json()
                if not isinstance(user, dict) or user.get('id') != target:
                    raise _pending()
        except (ValueError, TypeError):
            raise _pending() from None
        finally:
            response.close()
