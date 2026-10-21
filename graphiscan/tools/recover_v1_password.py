"""Operator-only disposable-fixture recovery. Stop all API workers first.

Fixed fictional account, hidden intended-new-password prompt, no password write.
Only confirms a pending operation after new-password sign-in and global sign-out.
Never use while a timed-out worker/provider write might still be executing.
"""
import getpass
import json
import sys
import warnings
from pathlib import Path
from uuid import UUID, uuid4

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from v1_backend import SupabasePostgresBackend, backend_from_environment

TEST_EMAIL = 'graphiscan.test@example.invalid'


def recover(backend, operation, new_password):
    UUID(operation)
    service = backend.password_service
    if service is None or not new_password:
        return False
    provider = service.provider
    bearer = None
    signed_out = False
    try:
        result = provider.call('POST', '/token?grant_type=password',
                               body={'email': TEST_EMAIL, 'password': new_password})
        bearer = result.get('access_token')
        if not isinstance(bearer, str) or not bearer:
            return False
        identity = backend.authenticate(bearer)
        user = provider.call('GET', '/user', bearer=bearer)
        if user.get('id') != identity.user_id or user.get('email', '').lower() != TEST_EMAIL:
            return False
        # An operator confirms the intended new password, rather than clearing
        # pending based on the original session or a guessed provider outcome.
        provider.sign_out_all(bearer)
        signed_out = True
        service.repository.complete(identity, operation, str(uuid4()))
        return True
    except Exception:
        return False
    finally:
        if bearer and not signed_out:
            try:
                provider.call('POST', '/logout?scope=local', bearer=bearer, expected=204)
            except Exception:
                pass  # Output remains fixed; runbook requires cleanup on failure.


def main():
    if len(sys.argv) != 1 or not sys.stdin.isatty():
        print(json.dumps({'status': 'blocked', 'reason': 'Use an interactive terminal without arguments.'}))
        return 2
    from dotenv import load_dotenv
    load_dotenv(APP_ROOT / '.env', override=False)
    backend = backend_from_environment()
    if not isinstance(backend, SupabasePostgresBackend) or backend.password_service is None:
        print(json.dumps({'status': 'blocked', 'reason': 'Separate password writer configuration is required.'}))
        return 2
    try:
        if input('After stopping API workers and resolving outstanding provider requests, type WORKERS STOPPED: ') != 'WORKERS STOPPED':
            return 2
        operation = str(UUID(input('Pending fictional operation UUID (not a credential): ').strip()))
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            password = getpass.getpass('Intended NEW fictional Auth password (hidden): ')
        success = recover(backend, operation, password)
        password = None
    except (Exception, KeyboardInterrupt):
        success = False
    print(json.dumps({'status': 'recovered-sign-in-required' if success else 'recovery-not-confirmed',
                      'credentials_saved': False}))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
