"""Read-only post-015 checks; no Auth credentials, record output or mutations."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from v1_backend import SupabasePostgresBackend, backend_from_environment
from tools.check_v1_hosted import CONNECTION_SQL

FIXTURE_SQL = """WITH wanted(full_name,role) AS (VALUES
    ('Synthetic Test Admin','admin'),('Synthetic Test Teacher','teacher'),
    ('Synthetic Test Expert','expert'),('Synthetic Test Parent','parent')),
people AS (SELECT p.* FROM public.user_profiles p JOIN wanted w USING(full_name,role)),
notice AS (SELECT * FROM public.privacy_agreements WHERE is_current)
SELECT (SELECT count(*)=4 AND count(DISTINCT role)=4 AND bool_and(account_status='active') FROM people) AS profiles,
    (SELECT count(*)=1 AND bool_and(version='graphiscan-workflow-test-v1'
        AND test_subject_id IS NULL AND cardinality(test_subject_ids)=4
        AND test_subject_ids @> ARRAY(SELECT user_id FROM people)
        AND content_sha256=%s AND content_sha256=encode(sha256(convert_to(content,'UTF8')),'hex')
        AND approved_by IN (SELECT user_id FROM people WHERE role='admin')
        AND published_at<=clock_timestamp() AND approved_at<=clock_timestamp()) FROM notice) AS exact_notice,
    (SELECT count(*)=1 AND bool_and(NOT is_current AND test_subject_ids IS NULL
        AND test_subject_id IN (SELECT user_id FROM people WHERE role='admin')
        AND content_sha256=encode(sha256(convert_to(content,'UTF8')),'hex'))
        FROM public.privacy_agreements WHERE version='graphiscan-test-v1') AS old_notice_retained,
    (SELECT count(*)=1 AND bool_and(g.permission_key='assignments.manage' AND g.school_id IS NOT NULL
        AND g.user_id IN (SELECT user_id FROM people WHERE role='admin'))
        FROM public.user_permission_grants g WHERE user_id IN (SELECT user_id FROM people)) AS narrow_grant,
    (SELECT count(*)=2 AND count(DISTINCT p.role)=2 AND bool_and(p.role IN ('teacher','expert')
        AND m.school_id IN (SELECT school_id FROM public.user_permission_grants
            WHERE user_id IN (SELECT user_id FROM people WHERE role='admin') AND permission_key='assignments.manage'))
        FROM public.school_memberships m
        JOIN people p ON p.user_id=m.user_id) AS memberships"""


def run(connect=False):
    report = {'status': 'blocked', 'checks': [], 'database_writes': False,
              'network_attempted': False, 'scope': '015 metadata, notice and reader-visible fixture scope only'}
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
                if not all([check('connection_' + name, info.get(name)) for name in ('read_only', 'utc', 'bounded', 'restricted')]):
                    return report
                cursor.execute("""SELECT EXISTS (SELECT 1 FROM pg_attribute WHERE
                    attrelid='public.privacy_agreements'::regclass AND attname='test_subject_ids'
                    AND atttypid='uuid[]'::regtype AND NOT attisdropped) AS installed""")
                if not check('audience_column', (cursor.fetchone() or {}).get('installed')):
                    return report
                notice = (APP / 'api/fictional-workflow-notice.txt').read_text(encoding='utf-8')
                cursor.execute(FIXTURE_SQL, (hashlib.sha256(notice.encode()).hexdigest(),))
                info = cursor.fetchone() or {}
                if not all([check(name, info.get(name)) for name in ('profiles', 'exact_notice', 'old_notice_retained', 'narrow_grant', 'memberships')]):
                    return report
                signatures = [
                    ('graphiscan_accept_privacy(uuid,uuid,text,uuid)', False, True),
                    ('graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)', True, False),
                    ('graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)', True, False)]
                for name, reader, writer in signatures:
                    cursor.execute("""SELECT p.prosecdef AND p.proconfig @> ARRAY['search_path=pg_catalog']
                        AND p.prosrc LIKE '%%a.test_subject_ids%%' AS guarded,
                        has_function_privilege(current_user,p.oid,'EXECUTE')=%s AS reader_correct,
                        has_function_privilege('graphiscan_password_writer',p.oid,'EXECUTE')=%s AS writer_correct,
                        NOT has_function_privilege('anon',p.oid,'EXECUTE') AND
                        NOT has_function_privilege('authenticated',p.oid,'EXECUTE') AND
                        NOT has_function_privilege('service_role',p.oid,'EXECUTE') AS clients_denied
                        FROM pg_proc p WHERE p.oid=to_regprocedure(%s)""", (reader, writer, 'public.' + name))
                    info = cursor.fetchone() or {}
                    if not all([check(name.split('(')[0] + '_' + key, info.get(key))
                                for key in ('guarded', 'reader_correct', 'writer_correct', 'clients_denied')]):
                        return report
        report['status'] = 'workflow-setup-preflight-passed'
    except Exception:
        check('workflow_setup_checks', False)
        report['status'] = 'failed'
    return report


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv(APP / '.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connect', action='store_true')
    report = run(parser.parse_args().connect)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report['status'] in {'ready-to-connect', 'workflow-setup-preflight-passed'} else 1)
