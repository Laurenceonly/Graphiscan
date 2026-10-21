"""Read-only catalogue/grant check for the 013+014 bundle; no mutation probes."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from v1_backend import SupabasePostgresBackend,backend_from_environment
from tools.check_v1_hosted import CONNECTION_SQL

READS=['graphiscan_model_catalogue(uuid,uuid,bigint,integer)','graphiscan_screening_request(uuid,uuid,text)','graphiscan_screening_image(uuid,uuid,bigint)']
WRITES=['graphiscan_write_review(uuid,uuid,bigint,jsonb,text,uuid)','graphiscan_assign_expert(uuid,uuid,bigint,jsonb,uuid)',
    'graphiscan_reserve_screening(uuid,uuid,jsonb,text,jsonb,text,uuid)','graphiscan_complete_screening(uuid,uuid,text,jsonb,uuid)',
    'graphiscan_fail_screening(uuid,text,text)','graphiscan_screening_cleanup(text,bigint,boolean)']
SQL="""SELECT p.prosecdef AND p.proconfig @> ARRAY['search_path=pg_catalog'] AS safe,
    has_function_privilege('graphiscan_api_reader',p.oid,'EXECUTE') AS reader,
    has_function_privilege('graphiscan_password_writer',p.oid,'EXECUTE') AS writer,
    NOT has_function_privilege('anon',p.oid,'EXECUTE') AND
    NOT has_function_privilege('authenticated',p.oid,'EXECUTE') AND
    NOT has_function_privilege('service_role',p.oid,'EXECUTE') AND
    NOT EXISTS(SELECT 1 FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
        WHERE a.grantee=0 AND a.privilege_type='EXECUTE') AS clients_denied
    FROM pg_proc p WHERE p.oid=to_regprocedure(%s)"""
def run(connect=False):
    report={'status':'blocked','checks':[],'network_attempted':False,'database_writes':False,'scope':'bundle catalogue/grants and nonexistent-identity reads only'}
    def check(name,ok):report['checks'].append({'name':name,'status':'pass' if ok else 'fail'});return ok
    try:
        backend=backend_from_environment()
        if not check('adapter_configured',isinstance(backend,SupabasePostgresBackend)):return report
        if not connect:report['status']='ready-to-connect';return report
        report['network_attempted']=True
        with backend.repository.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(CONNECTION_SQL);info=cursor.fetchone() or {}
                if not all([check('connection_'+k,info.get(k) is True) for k in ('read_only','utc','bounded','restricted')]):return report
                for signature in READS+WRITES:
                    cursor.execute(SQL,('public.'+signature,));row=cursor.fetchone() or {};read=signature in READS
                    if not check(signature,row.get('safe') is True and row.get('clients_denied') is True and row.get('reader') is read and row.get('writer') is (not read)):return report
                for role in ('graphiscan_api_reader','graphiscan_password_writer'):
                    cursor.execute("SELECT NOT has_table_privilege(%s,'public.screening_upload_jobs','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS denied",(role,))
                    if not check(role+'_no_upload_job_table_access',(cursor.fetchone() or {}).get('denied') is True):return report
                zero='00000000-0000-0000-0000-000000000000'
                for name,sql,args in [
                    ('models',"SELECT public.graphiscan_model_catalogue(%s::uuid,%s::uuid,NULL,1) result",(zero,zero)),
                    ('request',"SELECT public.graphiscan_screening_request(%s::uuid,%s::uuid,%s) result",(zero,zero,'nonexistent-upload-key-0001')),
                    ('image',"SELECT public.graphiscan_screening_image(%s::uuid,%s::uuid,1) result",(zero,zero))]:
                    cursor.execute(sql,args);data=(cursor.fetchone() or {}).get('result') or {}
                    if not check(name+'_unissued_identity_denied',data.get('code')=='AUTHENTICATION_REQUIRED'):return report
        report['status']='screening-write-preflight-passed'
    except Exception:check('hosted_checks',False);report['status']='failed'
    return report
if __name__=='__main__':
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env');parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--connect',action='store_true');args=parser.parse_args()
    report=run(args.connect);print(json.dumps(report,indent=2));sys.exit(0 if report['status'] in {'ready-to-connect','screening-write-preflight-passed'} else 1)
