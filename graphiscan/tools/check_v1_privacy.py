"""Manual fictional-account notice display/acceptance check; no password change.

Only writes acceptance after the exact test notice is displayed and explicitly
accepted in the terminal. Never saves or prints credentials or Auth sessions.
"""
import getpass
import json
import sys
import warnings
from pathlib import Path

APP_ROOT=Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0,str(APP_ROOT))

from flask import Flask, jsonify
from api_v1 import InvalidSession, install_api_v1, require_access
from v1_backend import SupabasePostgresBackend, backend_from_environment

EMAIL='graphiscan.test@example.invalid'
VERSION='graphiscan-test-v1'
NOTICE=(APP_ROOT/'api/test-notice-v1.txt').read_text(encoding='utf8')


def run_check(password,backend,*,ask=input,show=print):
    report={'status':'blocked','checks':[],'acceptance_attempted':False,'credentials_saved':False}
    bearer=identity=None
    provider=None
    def record(name,passed):
        report['checks'].append({'name':name,'status':'pass' if passed else 'fail'})
        return passed
    try:
        if not record('adapter_configured',isinstance(backend,SupabasePostgresBackend) and
                      backend.password_service is not None and backend.privacy_service is not None):
            return report
        provider=backend.password_service.provider
        result=provider.call('POST','/token?grant_type=password',body={'email':EMAIL,'password':password})
        bearer=result.get('access_token')
        if not isinstance(bearer,str) or not bearer:
            raise ValueError()
        identity=backend.authenticate(bearer)
        user=provider.call('GET','/user',bearer=bearer)
        if not record('fictional_subject_verified',user.get('id')==identity.user_id and user.get('email')==EMAIL):
            return report
        app=Flask('graphiscan-fictional-notice-check')
        install_api_v1(app,backend)
        app.add_url_rule('/api/v1/test-notice-gate','api_v1.notice_probe',require_access()(lambda:jsonify(data={'ok':True})))
        with app.test_client() as client:
            headers={'Authorization':'Bearer '+bearer}
            response=client.get('/api/v1/privacy-agreement',headers=headers)
            notice=(response.get_json() or {}).get('data',{})
            if not record('exact_test_notice',response.status_code==200 and notice.get('version')==VERSION and
                          notice.get('content','').replace('\r\n','\n')==NOTICE.replace('\r\n','\n')):
                return report
            # Only canonical, nonprivate notice text is printed for review.
            show(notice['content'])
            if ask('To accept fictional testing only, type ACCEPT TEST NOTICE: ')!='ACCEPT TEST NOTICE':
                report['status']='declined'
                return report
            report['acceptance_attempted']=True
            body={'agreement_version':VERSION,'accepted':True}
            accepted=client.post('/api/v1/me/privacy-acceptance',headers=headers,json=body)
            data=(accepted.get_json() or {}).get('data',{})
            if not record('acceptance_saved',accepted.status_code==200 and data.get('agreement_version')==VERSION and
                          isinstance(data.get('accepted_at'),str) and accepted.headers.get('Cache-Control')=='no-store'):
                return report
            repeated=client.post('/api/v1/me/privacy-acceptance',headers=headers,json=body)
            record('repeat_preserves_timestamp',repeated.status_code==200 and (repeated.get_json() or {}).get('data')==data)
            stale=client.post('/api/v1/me/privacy-acceptance',headers=headers,json={'agreement_version':'stale-test-v0','accepted':True})
            record('stale_version_denied',stale.status_code==409 and
                   (stale.get_json() or {}).get('error',{}).get('code')=='AGREEMENT_CHANGED')
            me=client.get('/api/v1/me',headers=headers)
            state=(me.get_json() or {}).get('data',{}).get('onboarding',{})
            record('bootstrap_ready',me.status_code==200 and state.get('accepted_agreement_version')==VERSION and state.get('next_action')=='ready')
            record('gate_probe_ready',client.get('/api/v1/test-notice-gate',headers=headers).status_code==200)
    except Exception:
        record('privacy_check_completed',False)
    finally:
        if bearer:
            cleaned=False
            try:
                provider.call('POST','/logout?scope=local',bearer=bearer,expected=204)
                if identity is not None:
                    try:
                        backend.load_access(identity)
                    except InvalidSession:
                        cleaned=True
                else:
                    cleaned=True
            except Exception:
                pass
            record('test_session_cleanup',cleaned)
        if report['status']!='declined':
            report['status']='privacy-check-passed' if report['acceptance_attempted'] and all(
                row['status']=='pass' for row in report['checks']) else 'failed' if bearer else 'blocked'
        elif report['checks'][-1]['status']=='fail':
            report['status']='failed'
    return report


def main():
    if len(sys.argv)!=1 or not sys.stdin.isatty():
        print(json.dumps({'status':'blocked','reason':'Use an interactive terminal without arguments.'}))
        return 2
    from dotenv import load_dotenv
    load_dotenv(APP_ROOT/'.env',override=False)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',getpass.GetPassWarning)
            password=getpass.getpass('CURRENT fictional Auth password (hidden; no password change): ')
        report=run_check(password,backend_from_environment())
        password=None
    except (Exception,KeyboardInterrupt):
        print(json.dumps({'status':'not-confirmed','reason':'Interactive test did not complete.'}))
        return 1
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='privacy-check-passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
