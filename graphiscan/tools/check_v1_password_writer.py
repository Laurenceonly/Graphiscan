"""Read-only writer login/catalog preflight; never calls mutation functions."""
import argparse
import json
import os
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from v1_backend import SupabasePostgresBackend, backend_from_environment

WRITER_CONNECTION_SQL = """SELECT
    current_user = 'graphiscan_password_writer' AS expected_role,
    current_setting('transaction_read_only') = 'on' AS read_only,
    current_setting('TimeZone') = 'UTC' AS utc,
    current_setting('statement_timeout')::interval BETWEEN interval '1 millisecond' AND interval '5 seconds' AS bounded,
    current_setting('lock_timeout')::interval BETWEEN interval '1 millisecond' AND interval '3 seconds' AS bounded_lock,
    NOT (r.rolsuper OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication OR r.rolbypassrls OR r.rolinherit) AS restricted,
    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m WHERE m.member = r.oid) AS no_memberships,
    NOT has_schema_privilege(current_user, 'public', 'CREATE') AS no_schema_create
    FROM pg_catalog.pg_roles r WHERE r.rolname = current_user"""

WRITER_TABLES_SQL = """SELECT
    EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relname='password_change_operations' AND c.relrowsecurity) AS operation_rls,
    NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname IN ('public','auth') AND c.relkind IN ('r','p','v','m','f')
          AND (has_table_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
               OR c.relowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user))
    ) AS no_direct_tables,
    NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname IN ('public','auth') AND c.relkind='S'
          AND has_sequence_privilege(current_user,c.oid,'USAGE,SELECT,UPDATE')
    ) AS no_sequences"""

WRITER_FUNCTION_SQL = """SELECT p.prosecdef AS definer,
    p.proconfig @> ARRAY['search_path=pg_catalog'] AS fixed_path,
    has_function_privilege(current_user,p.oid,'EXECUTE') AS writer_allowed,
    NOT (has_function_privilege('anon',p.oid,'EXECUTE') OR
         has_function_privilege('authenticated',p.oid,'EXECUTE') OR
         has_function_privilege('service_role',p.oid,'EXECUTE') OR
         has_function_privilege('graphiscan_api_reader',p.oid,'EXECUTE')) AS clients_reader_denied,
    p.proowner <> (SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user) AS not_owner
    FROM pg_catalog.pg_proc p WHERE p.oid=to_regprocedure(%s)"""


def run_preflight(*, connect=False, environ=None, backend_factory=backend_from_environment):
    env = os.environ if environ is None else environ
    report = {'status': 'blocked', 'checks': [], 'network_attempted': False, 'database_writes': False,
              'scope': 'writer login/catalog metadata only; no Auth password change'}

    def record(name, passed):
        report['checks'].append({'name': name, 'status': 'pass' if passed else 'fail'})
        return passed

    if not record('writer_setting_present', bool(env.get('GRAPHISCAN_V1_PASSWORD_DATABASE_URL', ''))):
        return report
    try:
        backend = backend_factory(env)
        if not record('writer_adapter_configured', isinstance(backend, SupabasePostgresBackend)
                      and backend.password_service is not None):
            return report
        if not connect:
            report['status'] = 'ready-to-connect'
            return report
        report['network_attempted'] = True
        with backend.password_service.repository.connect() as connection:
            with connection.cursor() as cursor:
                # The writer normally allows mutations through two functions;
                # this preflight explicitly starts a read-only transaction.
                cursor.execute('SET TRANSACTION READ ONLY')
                for query, names, parameters in [
                    (WRITER_CONNECTION_SQL, ('expected_role', 'read_only', 'utc', 'bounded', 'bounded_lock',
                                             'restricted', 'no_memberships', 'no_schema_create'), None),
                    (WRITER_TABLES_SQL, ('operation_rls', 'no_direct_tables', 'no_sequences'), None),
                    *[(WRITER_FUNCTION_SQL, ('definer', 'fixed_path', 'writer_allowed', 'clients_reader_denied', 'not_owner'),
                       (signature,)) for signature in ('public.graphiscan_begin_password(uuid,uuid,uuid,uuid)',
                                                     'public.graphiscan_complete_password(uuid,uuid,uuid)')],
                ]:
                    if parameters is None:
                        cursor.execute(query)
                    else:
                        cursor.execute(query, parameters)
                    row = cursor.fetchone() or {}
                    prefix = 'complete_' if parameters and 'complete_' in parameters[0] else 'begin_' if parameters else ''
                    valid = [record(prefix + name, row.get(name) is True) for name in names]
                    if not all(valid):
                        report['status'] = 'failed'
                        return report
        report['status'] = 'writer-preflight-passed'
    except Exception:
        # No exception strings, DSNs, credentials, SQL rows or private profiles.
        record('writer_connection_or_catalog', False)
        report['status'] = 'failed'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connect', action='store_true')
    args = parser.parse_args()
    from dotenv import load_dotenv
    load_dotenv(APP_ROOT / '.env', override=False)
    report = run_preflight(connect=args.connect)
    print(json.dumps(report, indent=2))
    return 0 if report['status'] in ('ready-to-connect', 'writer-preflight-passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
