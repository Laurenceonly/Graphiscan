"""Interactive fictional Auth password change through the v1 Flask endpoint.

Intentionally changes the fixture's Auth password, clears its first-change flag
and revokes its sessions. Never uses/changes database-role passwords. No retries.
"""
import getpass
import json
import sys
import warnings
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from flask import Flask, jsonify
from api_v1 import ApiError, InvalidSession, install_api_v1, require_access
from v1_backend import SupabasePostgresBackend, backend_from_environment
from v1_password import validate_password_change

TEST_EMAIL = 'graphiscan.test@example.invalid'


def run_password_check(current, new, confirm, backend):
    report = {'status': 'blocked', 'checks': [], 'password_change_attempted': False,
              'application_writes_may_have_occurred': False, 'credentials_saved': False,
              'scope': 'fixed fictional Auth account; standalone Flask v1 endpoint'}
    sessions = []
    provider = None

    def record(name, passed):
        report['checks'].append({'name': name, 'status': 'pass' if passed else 'fail'})
        return passed

    def sign_in(password):
        result = provider.call('POST', '/token?grant_type=password',
                               body={'email': TEST_EMAIL, 'password': password})
        token = result.get('access_token')
        if not isinstance(token, str) or not token:
            raise ValueError()
        # Track immediately for cleanup even if verification/binding fails.
        entry = {'token': token, 'identity': None, 'provider_revoked': False}
        sessions.append(entry)
        identity = backend.authenticate(token)
        entry['identity'] = identity
        user = provider.call('GET', '/user', bearer=token)
        if user.get('id') != identity.user_id or user.get('email', '').lower() != TEST_EMAIL:
            raise ValueError()
        return entry

    def headers(session):
        return {'Authorization': 'Bearer ' + session['token']}

    try:
        if not record('writer_adapter_configured', isinstance(backend, SupabasePostgresBackend)
                      and backend.password_service is not None):
            return report
        body = {'current_password': current, 'new_password': new, 'confirm_password': confirm}
        try:
            validate_password_change(body)
        except ApiError:
            record('password_inputs_valid', False)
            return report
        record('password_inputs_valid', True)
        provider = backend.password_service.provider
        original = sign_in(current)
        other = sign_in(current)
        if not record('two_verified_fictional_sessions', original['identity'].user_id == other['identity'].user_id
                      and original['identity'].session_id != other['identity'].session_id):
            return report
        app = Flask('graphiscan-fictional-password-check')
        install_api_v1(app, backend)

        @require_access()
        def protected_probe():
            return jsonify(data={'ok': True})

        app.add_url_rule('/api/v1/test-password-gate', 'api_v1.password_gate', protected_probe)
        with app.test_client() as client:
            initial = client.get('/api/v1/me', headers=headers(original))
            profile = (initial.get_json() or {}).get('data', {})
            if not record('forced_password_fixture', initial.status_code == 200 and
                          profile.get('user_id') == original['identity'].user_id and
                          profile.get('full_name') == 'Synthetic Test Admin' and profile.get('role') == 'admin' and
                          profile.get('permissions') == [] and profile.get('school_ids') == [] and
                          profile.get('onboarding', {}).get('must_change_password') is True):
                return report
            denied = client.get('/api/v1/test-password-gate', headers=headers(original))
            if not record('initial_password_gate', denied.status_code == 403 and
                          (denied.get_json() or {}).get('error', {}).get('code') == 'PASSWORD_CHANGE_REQUIRED'):
                return report
            report['password_change_attempted'] = True
            report['application_writes_may_have_occurred'] = True
            changed = client.post('/api/v1/me/password', headers=headers(original), json=body)
            if not record('password_change_endpoint', changed.status_code == 200 and
                          (changed.get_json() or {}).get('data') == {'success': True, 'next_action': 'sign_in'} and
                          changed.headers.get('Cache-Control') == 'no-store'):
                report['recovery_required'] = True
                return report
            original['provider_revoked'] = other['provider_revoked'] = True
            for name, session in [('original_session_denied', original), ('other_session_denied', other)]:
                response = client.get('/api/v1/me', headers=headers(session))
                if not record(name, response.status_code == 401):
                    return report
            # One old-password probe; allowlisted credential denial only.
            try:
                sign_in(current)
            except ApiError as error:
                old_denied = error.code == 'CURRENT_PASSWORD_INVALID'
            else:
                old_denied = False
            if not record('old_password_denied', old_denied):
                return report
            fresh = sign_in(new)
            response = client.get('/api/v1/me', headers=headers(fresh))
            data = (response.get_json() or {}).get('data', {})
            onboarding = data.get('onboarding', {})
            if not record('fresh_new_password_bootstrap', response.status_code == 200 and
                          data.get('user_id') == original['identity'].user_id and
                          onboarding.get('must_change_password') is False):
                return report
            # The fixture has no consent; changing a password must never grant it.
            probe = client.get('/api/v1/test-password-gate', headers=headers(fresh))
            record('privacy_gate_preserved', probe.status_code in (403, 503) and
                   (probe.get_json() or {}).get('error', {}).get('code') in
                   ('PRIVACY_ACCEPTANCE_REQUIRED', 'AGREEMENT_NOT_CONFIGURED'))
    except Exception:
        record('password_check_completed', False)
    finally:
        cleanup_ok = True
        for session in sessions:
            # Skip provider cleanup only after confirmed global sign-out, never
            # just because the application's pending gate denies a session.
            denied = False
            if session['provider_revoked'] and session['identity'] is not None:
                try:
                    backend.load_access(session['identity'])
                except InvalidSession:
                    denied = True
                except Exception:
                    pass
            if not denied:
                try:
                    provider.call('POST', '/logout?scope=local', bearer=session['token'], expected=204)
                    if session['identity'] is None:
                        denied = True  # Provider cleanup confirmed, no trusted ID to probe.
                    else:
                        try:
                            backend.load_access(session['identity'])
                        except InvalidSession:
                            denied = True
                except Exception:
                    pass
            cleanup_ok = cleanup_ok and denied
        if sessions:
            record('test_sessions_cleanup', cleanup_ok)
        if report['checks'] and all(row['status'] == 'pass' for row in report['checks']) and report['password_change_attempted']:
            report['status'] = 'password-check-passed'
        elif report['status'] != 'blocked' or sessions:
            report['status'] = 'failed'
    return report


def main():
    if len(sys.argv) != 1 or not sys.stdin.isatty():
        print(json.dumps({'status': 'blocked', 'reason': 'Use an interactive terminal without arguments.'}))
        return 2
    from dotenv import load_dotenv
    load_dotenv(APP_ROOT / '.env', override=False)
    backend = backend_from_environment()
    if not isinstance(backend, SupabasePostgresBackend) or backend.password_service is None:
        print(json.dumps({'status': 'blocked', 'reason': 'Verified reader and separate writer configuration are required.'}))
        return 2
    print('This changes only the fictional Auth account password and revokes its sessions. Database passwords stay unchanged.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            current = getpass.getpass('CURRENT fictional Auth account password (hidden): ')
            new = getpass.getpass('NEW fictional Auth account password; save privately (hidden): ')
            confirm = getpass.getpass('Confirm NEW fictional Auth account password (hidden): ')
        report = run_password_check(current, new, confirm, backend)
        current = new = confirm = None
    except (Exception, KeyboardInterrupt):
        print(json.dumps({'status': 'not-confirmed', 'reason': 'Interactive check did not complete; do not automatically retry.'}))
        return 1
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'password-check-passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
