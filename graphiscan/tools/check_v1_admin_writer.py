"""Offline by default; --connect checks 017 catalog and optional writer login read-only."""
import argparse
import json
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from v1_backend import SupabasePostgresBackend, backend_from_environment
from tools.check_v1_hosted import CONNECTION_SQL

CATALOG_SQL = (APP / 'db/postgres/017_account_management_preflight.sql').read_text(encoding='utf-8')
SIGNATURE = 'public.graphiscan_update_account(uuid,uuid,uuid,jsonb,uuid)'


def run(connect=False, require_assignment_access=False):
    report = {'status': 'blocked', 'checks': [], 'database_writes': False,
              'network_attempted': False, 'scope': '017 and optional018-020 catalogs; read-only writer login; no records',
              'assignment_access_required': require_assignment_access}

    def check(name, value):
        report['checks'].append({'name': name, 'status': 'pass' if value is True else 'fail'})
        return value is True

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
                if not all([check('reader_' + name, info.get(name))
                            for name in ('read_only', 'utc', 'bounded', 'restricted')]):
                    return report
                cursor.execute('SELECT to_regprocedure(%s) IS NOT NULL AS installed', (SIGNATURE,))
                if not check('migration_017_installed', (cursor.fetchone() or {}).get('installed')):
                    report['status'] = 'migration-required'
                    return report
                cursor.execute(CATALOG_SQL)
                info = cursor.fetchone() or {}
                names = ('restricted_role', 'no_role_memberships', 'bounded_schema_access',
                         'no_direct_table_access', 'no_direct_sequence_access', 'guarded_update_function',
                         'writer_can_update', 'other_runtime_roles_denied', 'public_denied',
                         'other_application_functions_denied')
                if not all([check(name, info.get(name)) for name in names]):
                    return report
                cursor.execute("SELECT to_regprocedure('public.graphiscan_begin_account_issuance(uuid,uuid,uuid,jsonb)') IS NOT NULL OR to_regprocedure('public.graphiscan_complete_account_issuance(uuid,uuid,uuid,uuid,uuid)') IS NOT NULL AS installed")
                issuance_installed = (cursor.fetchone() or {}).get('installed') is True
                report['account_issuance_migration_installed'] = issuance_installed
                if issuance_installed:
                    cursor.execute((APP / 'db/postgres/018_account_issuance_preflight.sql').read_text(encoding='utf-8'))
                    issuance_info = cursor.fetchone() or {}
                    issuance_names = ('issuance_functions_installed', 'guarded_issuance_functions',
                                      'writer_can_issue', 'issuance_other_roles_denied',
                                      'issuance_public_denied', 'issuance_table_protected')
                    if not all([check(name, issuance_info.get(name)) for name in issuance_names]):
                        return report
        service = getattr(backend, 'admin_write_service', None)
        with backend.repository.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT to_regprocedure('public.graphiscan_get_admin_account(uuid,uuid,uuid)') IS NOT NULL OR to_regprocedure('public.graphiscan_begin_admin_account_operation(uuid,uuid,uuid,uuid,text,bigint,uuid)') IS NOT NULL AS installed")
                lifecycle_installed = (cursor.fetchone() or {}).get('installed') is True
                report['account_lifecycle_migration_installed'] = lifecycle_installed
                if lifecycle_installed:
                    cursor.execute((APP / 'db/postgres/019_admin_account_lifecycle_preflight.sql').read_text(encoding='utf-8'))
                    info = cursor.fetchone() or {}
                    names = ('lifecycle_functions_installed', 'guarded_lifecycle_functions',
                             'lifecycle_exact_runtime_grants', 'lifecycle_public_denied', 'lifecycle_table_protected')
                    if not all([check(name, info.get(name)) for name in names]):
                        return report
                cursor.execute("SELECT to_regprocedure('public.graphiscan_get_assignment_access(uuid,uuid,uuid,uuid,bigint)') IS NOT NULL OR to_regprocedure('public.graphiscan_set_assignment_access(uuid,uuid,uuid,uuid,bigint,bigint,boolean,uuid)') IS NOT NULL AS installed")
                assignment_installed = (cursor.fetchone() or {}).get('installed') is True
                report['assignment_access_migration_installed'] = assignment_installed
                if require_assignment_access and not assignment_installed:
                    check('migration_020_installed', False)
                    report['status'] = 'migration-required'
                    return report
                if assignment_installed:
                    cursor.execute((APP / 'db/postgres/020_assignment_access_preflight.sql').read_text(encoding='utf-8'))
                    info = cursor.fetchone() or {}
                    names = ('assignment_functions_installed', 'assignment_guarded_functions',
                             'assignment_exact_runtime_grants', 'assignment_public_denied', 'assignment_table_protected')
                    if not all([check(name, info.get(name)) for name in names]):
                        return report
        if service is None:
            report['status'] = 'writer-configuration-required'
            return report
        with service.repository.connect() as connection:
            # The connector finishes its SET SESSION transaction before returning.
            # Start a read-only transaction before any catalog query on the writer.
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION READ ONLY')
                cursor.execute(CONNECTION_SQL)
                info = cursor.fetchone() or {}
                if not all([check('writer_' + name, info.get(name))
                            for name in ('read_only', 'utc', 'bounded', 'restricted')]):
                    return report
                cursor.execute("""SELECT current_user='graphiscan_admin_writer' AS exact_role,
                    current_setting('lock_timeout')::interval > interval '0 seconds'
                    AND current_setting('lock_timeout')::interval <= interval '3 seconds' AS lock_bounded""")
                info = cursor.fetchone() or {}
                if not all([check(name, info.get(name)) for name in ('exact_role', 'lock_bounded')]):
                    return report
        report['status'] = 'admin-writer-setup-passed'
    except Exception:
        check('admin_writer_checks', False)
        report['status'] = 'failed'
    return report


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv(APP / '.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connect', action='store_true')
    parser.add_argument('--require-assignment-access', action='store_true', help='Require020 instead of treating it as optional')
    args = parser.parse_args()
    report = run(args.connect, args.require_assignment_access)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report['status'] in {'ready-to-connect', 'admin-writer-setup-passed'} else 1)
