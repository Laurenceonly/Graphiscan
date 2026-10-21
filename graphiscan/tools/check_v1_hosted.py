"""Read-only hosted preflight. Offline by default; never prints config or records."""

import argparse
import json
import os
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from api_v1 import install_api_v1
from v1_backend import SNAPSHOT_SQL, SupabasePostgresBackend, backend_from_environment


SETTINGS = ("GRAPHISCAN_V1_BACKEND", "GRAPHISCAN_V1_SUPABASE_URL",
            "GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY", "GRAPHISCAN_V1_DATABASE_URL")
TABLES = ("public.user_profiles", "public.app_session_revocations",
          "public.privacy_agreements", "public.privacy_agreement_acceptances",
          "public.user_permission_grants", "public.school_memberships")

CONNECTION_SQL = """SELECT
    current_setting('transaction_read_only') = 'on' AS read_only,
    current_setting('TimeZone') = 'UTC' AS utc,
    current_setting('statement_timeout')::interval <= interval '5 seconds'
      AND current_setting('statement_timeout')::interval > interval '0 seconds' AS bounded,
    NOT (rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls) AS restricted
    FROM pg_catalog.pg_roles WHERE rolname = current_user"""

TABLE_ACCESS_SQL = """SELECT c.relrowsecurity AS rls,
    has_schema_privilege(current_user, n.oid, 'USAGE') AS schema_usage,
    has_table_privilege(current_user, c.oid, 'SELECT') AS can_select,
    has_table_privilege(current_user, c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS can_write,
    c.relowner = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user) AS owns_table
    FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
    WHERE c.oid=to_regclass(%s) AND c.relkind IN ('r','p')"""

TRIGGER_SQL = """SELECT EXISTS (
    SELECT 1 FROM pg_catalog.pg_trigger t
    JOIN pg_catalog.pg_proc p ON p.oid=t.tgfoid
    JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
    WHERE t.tgrelid='public.user_profiles'::regclass
      AND t.tgname='profile_session_invalidation' AND NOT t.tgisinternal
      AND t.tgenabled IN ('O','A') AND t.tgtype=19
      AND n.nspname='public' AND p.proname='invalidate_profile_sessions'
) AS installed"""

SESSION_FUNCTION_SQL = """SELECT EXISTS (
    SELECT 1 FROM pg_catalog.pg_proc p
    WHERE p.oid=to_regprocedure('public.graphiscan_session_state(uuid,uuid)')
      AND p.prosecdef AND p.provolatile='s'
      AND p.proconfig @> ARRAY['search_path=pg_catalog']
      AND has_function_privilege(current_user,p.oid,'EXECUTE')
      AND NOT has_function_privilege('anon',p.oid,'EXECUTE')
      AND NOT has_function_privilege('authenticated',p.oid,'EXECUTE')
) AS installed,
    coalesce((SELECT NOT has_table_privilege(current_user,c.oid,
        'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='auth' AND c.relname='sessions' AND c.relkind IN ('r','p')),
        false) AS auth_table_restricted"""


def run_preflight(environ=None, *, connect=False, backend_factory=backend_from_environment):
    env = os.environ if environ is None else environ
    report = {"mode": "read-only-connect" if connect else "offline", "status": "blocked",
              "checks": [], "network_attempted": False, "database_writes": False,
              "scope": "configuration and access preflight; not full hosted integration"}

    def record(name, passed):
        report["checks"].append({"name": name, "status": "pass" if passed else "fail"})
        return passed

    present = True
    for setting in SETTINGS:
        present = record(setting + "_present", bool(env.get(setting, "").strip())) and present
    if not present:
        return report
    try:
        backend = backend_factory(env)
        if not record("adapter_configuration", isinstance(backend, SupabasePostgresBackend)):
            return report
        if not connect:
            report["status"] = "ready-to-connect"
            return report

        report["network_attempted"] = True
        with backend.repository.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(CONNECTION_SQL)
                info = cursor.fetchone() or {}
                for name in ("read_only", "utc", "bounded", "restricted"):
                    if not record("connection_" + name, info.get(name) is True):
                        report["status"] = "failed"
                        return report
                # No queries against student/sample/result tables or raw provider
                # records. Catalog results are reduced to booleans only.
                for table in TABLES:
                    cursor.execute(TABLE_ACCESS_SQL, (table,))
                    access = cursor.fetchone() or {}
                    if not record(table + "_read_only_grants", bool(access) and
                                  access.get("schema_usage") is True and access.get("can_select") is True and
                                  access.get("can_write") is False and access.get("owns_table") is False):
                        report["status"] = "failed"
                        return report
                    if table.startswith("public.") and not record(table + "_rls_enabled", access.get("rls") is True):
                        report["status"] = "failed"
                        return report
                cursor.execute(TRIGGER_SQL)
                if not record("session_invalidation_trigger", (cursor.fetchone() or {}).get("installed") is True):
                    report["status"] = "failed"
                    return report
                cursor.execute(SESSION_FUNCTION_SQL)
                session_function = cursor.fetchone() or {}
                if not record("restricted_session_function", session_function.get("installed") is True and
                              session_function.get("auth_table_restricted") is True):
                    report["status"] = "failed"
                    return report
                # Execute the exact runtime query with deliberately nonexistent
                # identities. This validates columns/types/grants without reading
                # a real profile; a zero UUID must never establish access.
                cursor.execute(SNAPSHOT_SQL, {"user_id": "00000000-0000-0000-0000-000000000000",
                                              "session_id": "00000000-0000-0000-0000-000000000000"})
                snapshot = cursor.fetchone() or {}
                if not record("unissued_identity_denied", snapshot.get("session_valid") is False and snapshot.get("user_id") is None):
                    report["status"] = "failed"
                    return report

        bearer = env.get("GRAPHISCAN_V1_TEST_ACCESS_TOKEN", "")
        if bearer:
            from flask import Flask
            app = Flask("graphiscan-hosted-preflight")
            install_api_v1(app, backend)
            with app.test_client() as client:
                response = client.get("/api/v1/me", headers={"Authorization": "Bearer " + bearer})
                body = response.get_json() or {}
                if not record("test_session_bootstrap", response.status_code == 200 and
                              set(body.get("data", {})) == {"user_id", "full_name", "role", "account_status",
                                                           "permissions", "school_ids", "onboarding"} and
                              response.headers.get("Cache-Control") == "no-store"):
                    report["status"] = "failed"
                    return report
        else:
            report["checks"].append({"name": "test_session_bootstrap", "status": "not-run"})
        report["status"] = "preflight-passed"
    except Exception:
        # Do not stringify exceptions: DB/HTTP errors can include DSNs, bearer
        # headers, SQL parameters or other private fields. No traceback by design.
        record("hosted_read_checks", False)
        report["status"] = "failed"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connect", action="store_true", help="Run read-only checks against the configured disposable target")
    args = parser.parse_args(argv)
    from dotenv import load_dotenv
    load_dotenv(APP_ROOT / ".env", override=False)
    report = run_preflight(connect=args.connect)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] in ("ready-to-connect", "preflight-passed") else 2 if report["status"] == "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
