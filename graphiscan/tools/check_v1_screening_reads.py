"""Read-only migration-012 preflight; reports booleans, never records/config."""
import argparse
import json
from pathlib import Path
import sys

APP_ROOT=Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:sys.path.insert(0,str(APP_ROOT))
from v1_backend import SupabasePostgresBackend, backend_from_environment
from tools.check_v1_hosted import CONNECTION_SQL

SIGNATURE='public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'
METADATA_SQL="""SELECT p.prosecdef AS definer, p.provolatile='s' AS stable,
    p.proconfig @> ARRAY['search_path=pg_catalog'] AS fixed_path,
    has_function_privilege(current_user,p.oid,'EXECUTE') AS reader_execute,
    NOT has_function_privilege('anon',p.oid,'EXECUTE') AS anon_denied,
    NOT has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_denied,
    NOT has_function_privilege('service_role',p.oid,'EXECUTE') AS service_denied,
    NOT has_function_privilege('graphiscan_password_writer',p.oid,'EXECUTE') AS writer_denied,
    NOT EXISTS (SELECT 1 FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
                WHERE a.grantee=0 AND a.privilege_type='EXECUTE') AS public_denied
    FROM pg_proc p WHERE p.oid=to_regprocedure(%s)"""

def run(*, connect=False, backend_factory=backend_from_environment):
    report={'status':'blocked','checks':[],'network_attempted':False,'database_writes':False,
            'scope':'migration 012 metadata and nonexistent-identity denial only'}
    def check(name,passed):
        report['checks'].append({'name':name,'status':'pass' if passed else 'fail'})
        return passed
    try:
        backend=backend_factory()
        if not check('adapter_configured',isinstance(backend,SupabasePostgresBackend)):return report
        if not connect:
            report['status']='ready-to-connect';return report
        report['network_attempted']=True
        with backend.repository.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(CONNECTION_SQL)
                info=cursor.fetchone() or {}
                if not all([check('connection_'+key,info.get(key) is True) for key in ('read_only','utc','bounded','restricted')]):return report
                cursor.execute(METADATA_SQL,(SIGNATURE,))
                info=cursor.fetchone() or {}
                keys=('definer','stable','fixed_path','reader_execute','anon_denied','authenticated_denied','service_denied','writer_denied','public_denied')
                if not all([check(key,info.get(key) is True) for key in keys]):return report
                for table in ('screening_results','screening_reports','expert_validations','handwriting_samples'):
                    cursor.execute("SELECT NOT has_table_privilege(current_user,%s,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS denied",('public.'+table,))
                    if not check(table+'_direct_access_denied',(cursor.fetchone() or {}).get('denied') is True):return report
                for resource in ('screenings','screening','history','report'):
                    cursor.execute('''SELECT public.graphiscan_read_screenings(
                        %s::uuid,%s::uuid,%s::text,'{}'::jsonb,NULL::timestamptz,
                        NULL::bigint,25,1::bigint,false) AS result''',('00000000-0000-0000-0000-000000000000',)*2+(resource,))
                    data=(cursor.fetchone() or {}).get('result') or {}
                    if not check(resource+'_unissued_identity_denied',data.get('code')=='AUTHENTICATION_REQUIRED' and data.get('rows')==[]):return report
        report['status']='screening-read-preflight-passed'
    except Exception:
        check('hosted_read_checks',False)
        report['status']='failed'
    return report

if __name__=='__main__':
    from dotenv import load_dotenv
    load_dotenv(APP_ROOT/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connect',action='store_true',help='Explicit read-only hosted checks; no application rows printed.')
    args=parser.parse_args()
    report=run(connect=args.connect)
    print(json.dumps(report,indent=2))
    sys.exit(0 if report['status'] in {'ready-to-connect','screening-read-preflight-passed'} else 1)
