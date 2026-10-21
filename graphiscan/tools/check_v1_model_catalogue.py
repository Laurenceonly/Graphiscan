"""Interactive fictional-admin check of the running local model catalogue; no screening writes."""
import getpass
import json
from pathlib import Path
import sys
import warnings

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v1_backend import SupabasePostgresBackend,backend_from_environment
from v1_models import VersionedBinaryRuntime

EMAIL='graphiscan.test@example.invalid'
ORIGIN='http://127.0.0.1:5002/api/v1'


def run_check(password,backend):
    import requests
    report={'status':'blocked','checks':[],'credentials_saved':False,'screening_writes':False,
            'scope':'fixed fictional admin; running local API catalogue and temporary Auth session'}
    bearer=None;provider=None
    session=requests.Session();session.trust_env=False
    def check(name,passed):
        report['checks'].append({'name':name,'status':'pass' if passed else 'fail'})
        return passed
    def get(path,authenticated=True):
        return session.get(ORIGIN+path,headers={'Authorization':'Bearer '+bearer} if authenticated else {},
                           timeout=30,allow_redirects=False)
    try:
        if not check('adapter_configured',isinstance(backend,SupabasePostgresBackend) and backend.password_service is not None):
            return report
        service=backend.screening_upload_service
        if not check('three_pinned_models_and_storage_configured',isinstance(service.runtime,VersionedBinaryRuntime) and
                     len(service.runtime.entries)==3 and service.storage is not None):return report
        health=get('/health',False)
        if not check('running_api_ready',health.status_code==200):return report
        provider=backend.password_service.provider
        result=provider.call('POST','/token?grant_type=password',body={'email':EMAIL,'password':password})
        bearer=result.get('access_token')
        if not isinstance(bearer,str) or not bearer:raise ValueError()
        identity=backend.authenticate(bearer)
        user=provider.call('GET','/user',bearer=bearer)
        if not check('fictional_subject_verified',user.get('id')==identity.user_id and user.get('email')==EMAIL):return report
        me=get('/me');profile=(me.json() or {}).get('data',{})
        if not check('fictional_admin_ready',me.status_code==200 and profile.get('role')=='admin' and
                     profile.get('full_name')=='Synthetic Test Admin' and profile.get('onboarding',{}).get('next_action')=='ready'):
            return report
        response=get('/models?limit=100');body=response.json()
        if not check('catalogue_endpoint',response.status_code==200 and response.headers.get('Cache-Control')=='no-store' and
                     isinstance(body.get('data'),list) and body.get('page',{}).get('next_cursor') is None):return report
        rows=body['data']
        expected_accuracy={'resnet50':0.72794,'efficientnetb0':0.72794,'mobilenetv2':0.85294}
        for key,(entry,_) in service.runtime.entries.items():
            matches=[row for row in rows if row.get('model_key')==key and row.get('model_version')==entry['model_version']]
            if not check(key+'_published_and_installed',len(matches)==1 and service.runtime.supports(matches[0]) and
                         matches[0].get('is_selectable') is True and
                         abs(float((matches[0].get('evaluation') or {}).get('test_accuracy',-1))-expected_accuracy[key])<0.000001 and
                         (matches[0].get('evaluation') or {}).get('split_unit')=='image' and
                         (matches[0].get('evaluation') or {}).get('writer_separation_verified') is False):return report
        defaults=[row for row in rows if row.get('is_default')]
        check('mobilenetv2_unique_selectable_default',len(defaults)==1 and defaults[0].get('model_key')=='mobilenetv2' and defaults[0].get('is_selectable') is True)
        check('anonymous_catalogue_denied',get('/models',False).status_code==401)
    except Exception:
        check('catalogue_check_completed',False)
    finally:
        if bearer:
            cleaned=False
            try:
                provider.call('POST','/logout?scope=local',bearer=bearer,expected=204)
                cleaned=get('/models').status_code==401
            except Exception:pass
            check('test_session_cleanup',cleaned)
        session.close()
        report['status']='model-catalogue-check-passed' if report['checks'] and all(row['status']=='pass' for row in report['checks']) else 'failed' if bearer else 'blocked'
    return report


if __name__=='__main__':
    if len(sys.argv)!=1 or not sys.stdin.isatty():
        print(json.dumps({'status':'blocked','reason':'Use an interactive terminal without arguments.'}));sys.exit(2)
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',getpass.GetPassWarning)
            password=getpass.getpass('CURRENT fictional Auth password (hidden; no password change): ')
        report=run_check(password,backend_from_environment());password=None
        print(json.dumps(report,indent=2));sys.exit(0 if report['status']=='model-catalogue-check-passed' else 1)
    except (Exception,KeyboardInterrupt):
        print(json.dumps({'status':'not-confirmed','private_error_omitted':True}));sys.exit(1)
