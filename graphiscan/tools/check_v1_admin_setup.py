"""Read-only post-016 setup checks. Prints booleans, never credentials or rows."""
import argparse
import json
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from v1_backend import SupabasePostgresBackend, backend_from_environment
from tools.check_v1_hosted import CONNECTION_SQL

SIGNATURE = 'public.graphiscan_read_admin(uuid,uuid,text,text,text,text,timestamptz,uuid,bigint,integer)'


def run(connect=False):
    report = {'status': 'blocked', 'checks': [], 'database_writes': False,
              'network_attempted': False, 'scope': '016 metadata, denial gate and fictional admin read grants only'}

    def check(name, passed):
        report['checks'].append({'name': name, 'status': 'pass' if passed is True else 'fail'})
        return passed is True

    try:
        backend = backend_from_environment()
        if not check('adapter_configured', isinstance(backend, SupabasePostgresBackend)):
            return report
        if not connect:
            report['status'] = 'ready-to-connect'
            return report
        report['network_attempted'] = True
        with backend.repository.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(CONNECTION_SQL)
                info = cursor.fetchone() or {}
                if not all([check('connection_' + name, info.get(name))
                            for name in ('read_only', 'utc', 'bounded', 'restricted')]):
                    return report
                cursor.execute('SELECT to_regprocedure(%s) IS NOT NULL AS installed', (SIGNATURE,))
                if not check('migration_016_installed', (cursor.fetchone() or {}).get('installed')):
                    report['status'] = 'migration-required'
                    return report
                cursor.execute("""SELECT p.prosecdef AND p.provolatile='s'
                    AND p.proconfig @> ARRAY['search_path=pg_catalog'] AS guarded_function,
                    has_function_privilege(current_user,p.oid,'EXECUTE') AS reader_can_execute,
                    NOT has_function_privilege('anon',p.oid,'EXECUTE')
                    AND NOT has_function_privilege('authenticated',p.oid,'EXECUTE')
                    AND NOT has_function_privilege('service_role',p.oid,'EXECUTE')
                    AND NOT has_function_privilege('graphiscan_password_writer',p.oid,'EXECUTE') AS other_roles_denied,
                    NOT EXISTS (SELECT 1 FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
                        WHERE a.grantee=0 AND a.privilege_type='EXECUTE') AS public_denied
                    FROM pg_proc p WHERE p.oid=to_regprocedure(%s)""", (SIGNATURE,))
                info = cursor.fetchone() or {}
                if not all([check(name, info.get(name)) for name in
                            ('guarded_function', 'reader_can_execute', 'other_roles_denied', 'public_denied')]):
                    return report
                cursor.execute("""SELECT count(*)=2 AND bool_and(i.indisvalid AND i.indisready) AS indexes_ready
                    FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid
                    JOIN pg_namespace n ON n.oid=c.relnamespace
                    WHERE n.nspname='public' AND c.relname IN
                        ('user_profiles_admin_page_idx','audit_logs_admin_page_idx')""")
                if not check('page_indexes_ready', (cursor.fetchone() or {}).get('indexes_ready')):
                    return report
                cursor.execute("""SELECT public.graphiscan_read_admin(
                    '00000000-0000-0000-0000-000000000000'::uuid,
                    '00000000-0000-0000-0000-000000000000'::uuid,
                    'accounts','','',NULL,NULL,NULL,NULL,25) AS result""")
                result = (cursor.fetchone() or {}).get('result') or {}
                if not check('missing_identity_denied', result.get('code') == 'AUTHENTICATION_REQUIRED'
                             and result.get('rows') == []):
                    return report
                cursor.execute("""WITH fixture AS (SELECT p.user_id FROM public.user_profiles p
                    WHERE p.full_name='Synthetic Test Admin' AND p.role='admin' AND p.account_status='active'
                        AND EXISTS (SELECT 1 FROM public.privacy_agreements a WHERE a.is_current
                            AND a.version='graphiscan-workflow-test-v1' AND p.user_id=ANY(a.test_subject_ids)))
                    SELECT (SELECT count(*)=1 FROM fixture) AS single_test_admin,
                        (SELECT count(*)=2 AND count(DISTINCT permission_key)=2
                         FROM public.user_permission_grants WHERE user_id IN (SELECT user_id FROM fixture)
                            AND school_id IS NULL AND permission_key IN ('accounts.manage','audit.read')) AS read_grants""")
                info = cursor.fetchone() or {}
                if not all([check(name, info.get(name)) for name in ('single_test_admin', 'read_grants')]):
                    report['status'] = 'test-admin-grants-required'
                    return report
        report['status'] = 'admin-read-setup-passed'
    except Exception:
        check('admin_setup_checks', False)
        report['status'] = 'failed'
    return report


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv(APP / '.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connect', action='store_true')
    report = run(parser.parse_args().connect)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report['status'] in {'ready-to-connect', 'admin-read-setup-passed'} else 1)
