"""Server-only Auth issuance with a committed reservation and no write replay."""
import json
import logging
import re
from uuid import UUID

import requests

from api_v1 import ApiError, BackendUnavailable
from v1_admin_writes import ERRORS, _school_ids


def validate_creation(body, key):
    fields = {'full_name', 'email', 'role', 'temporary_password', 'school_ids'}
    if not isinstance(body, dict) or set(body) != fields:
        raise ApiError(422, 'INVALID_INPUT', 'Complete all account fields.')
    if any(not isinstance(body[field], str) for field in fields - {'school_ids'}):
        raise ApiError(422, 'INVALID_INPUT', 'Check the supplied account fields.')
    name = ' '.join(body['full_name'].split())
    email = body['email'].strip().lower()
    password = body['temporary_password']
    if (not 1 <= len(name) <= 200 or any(ord(c) < 32 or ord(c) == 127 for c in body['full_name'])
            or len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email)
            or body['role'] not in {'admin', 'researcher', 'teacher', 'parent', 'expert', 'guest'}):
        raise ApiError(422, 'INVALID_INPUT', 'Check the supplied account fields.')
    if (not 8 <= len(password) <= 128 or not all(re.search(pattern, password)
            for pattern in (r'[A-Z]', r'[a-z]', r'[0-9]', r'[^A-Za-z0-9]'))):
        raise ApiError(422, 'INVALID_PASSWORD', 'Use 8–128 characters with uppercase, lowercase, a number and a symbol.')
    try:
        if not isinstance(key, str) or str(UUID(key)) != key:
            raise ValueError()
    except (ValueError, TypeError):
        raise ApiError(422, 'IDEMPOTENCY_KEY_REQUIRED', 'Provide a valid account request ID.') from None
    return dict(full_name=name, email=email, role=body['role'], school_ids=_school_ids(body['school_ids']))


def _pending():
    return ApiError(503, 'ACCOUNT_CREATION_PENDING',
                    'Account creation could not be confirmed. Check the user list and contact the system operator before trying again.')


def _result(row):
    result = row.get('result') if isinstance(row, dict) else None
    if not isinstance(result, dict) or 'code' not in result:
        raise BackendUnavailable()
    code = result['code']
    if code is None:
        return result
    if code in ERRORS:
        status, message, action = ERRORS[code]
        raise ApiError(status, code, message, action)
    if code == 'EMAIL_UNAVAILABLE':
        raise ApiError(409, code, 'This email already has an account or an account request. Check the user list.')
    if code == 'ISSUANCE_CONFLICT':
        raise ApiError(409, code, 'This account request changed. Check the user list before continuing.')
    if code == 'ACCOUNT_CREATION_PENDING':
        raise _pending()
    raise BackendUnavailable()


class SupabaseAccountProvider:
    def __init__(self, verifier, secret, *, http=None):
        if not isinstance(secret, str) or not secret.startswith('sb_secret_'):
            raise ValueError('A server-only Supabase secret key is required')
        self.origin, self.secret = verifier.origin, secret
        self.http = http if http is not None else requests

    def create(self, fields, password, operation):
        # Never log response text, credentials or provider payloads. No retries.
        try:
            response = self.http.request('POST', self.origin + '/auth/v1/admin/users',
                headers={'apikey': self.secret},
                json={'email': fields['email'], 'password': password, 'email_confirm': True,
                      'app_metadata': {'graphiscan_issuance_id': operation}},
                timeout=(3.05, 8), allow_redirects=False)
        except requests.RequestException:
            raise _pending() from None
        try:
            if response.status_code not in (200, 201):
                logging.getLogger(__name__).error('auth_account_create_failed status=%s', response.status_code)
                raise _pending()
            user = response.json()
            if not isinstance(user, dict) or not isinstance(user.get('id'), str):
                raise _pending()
            target = str(UUID(user['id']))
            if (str(user.get('email', '')).lower() != fields['email'] or
                    user.get('app_metadata', {}).get('graphiscan_issuance_id') != operation):
                raise _pending()
            return target
        except (ValueError, TypeError, AttributeError):
            raise _pending() from None
        finally:
            response.close()


class AccountIssuanceService:
    def __init__(self, repository, provider):
        self.repository, self.provider = repository, provider

    def create(self, identity, body, key, request_id):
        fields = validate_creation(body, key)
        try:
            UUID(request_id)
        except (ValueError, TypeError):
            raise BackendUnavailable() from None
        # Missing migration/configuration fails before any provider operation.
        reservation = _result(self.repository.execute(
            'SELECT public.graphiscan_begin_account_issuance(%s::uuid,%s::uuid,%s::uuid,%s::jsonb) AS result',
            (identity.user_id, identity.session_id, key, json.dumps(fields))))
        if isinstance(reservation.get('data'), dict):
            return {'data': reservation['data']}
        if reservation.get('reserved') is not True:
            raise BackendUnavailable()
        try:
            target = self.provider.create(fields, body['temporary_password'], key)
            result = _result(self.repository.execute(
                'SELECT public.graphiscan_complete_account_issuance(%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid) AS result',
                (identity.user_id, identity.session_id, key, target, request_id)))
            if not isinstance(result.get('data'), dict) or result['data'].get('user_id') != target:
                raise _pending()
            return {'data': result['data']}
        except Exception:
            # An orphan Auth identity has no profile and cannot access the API.
            # Preserve reservation for operator reconciliation; never delete/retry.
            raise _pending() from None
