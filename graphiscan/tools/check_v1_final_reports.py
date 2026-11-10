"""Read-only migration030 metadata/source verification; no application rows."""
import argparse
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def run():
    import psycopg
    source = (ROOT / 'db/postgres/030_final_screening_reports.sql').read_text(encoding='utf-8')
    checks = {}
    try:
        with psycopg.connect(os.environ['GRAPHISCAN_V1_DATABASE_URL'], connect_timeout=8,
                             options='-c default_transaction_read_only=on -c statement_timeout=8000 -c lock_timeout=2000') as connection:
            with connection.cursor() as cursor:
                cursor.execute((ROOT / 'db/postgres/030_final_screening_reports_preflight.sql').read_text(encoding='utf-8'))
                checks.update(zip([column.name for column in cursor.description], cursor.fetchone()))
                for name, arguments in [('graphiscan_final_context', 'uuid,uuid,bigint'),
                                        ('graphiscan_read_final_report', 'uuid,uuid,bigint'),
                                        ('graphiscan_finalize_report', 'uuid,uuid,bigint,jsonb,text,uuid')]:
                    expected = re.search(r'CREATE FUNCTION public\.' + name + r'\(.*?AS \$\$(.*?)\$\$;', source, re.S).group(1)
                    cursor.execute('SELECT prosrc FROM pg_proc WHERE oid=to_regprocedure(%s)', ('public.' + name + '(' + arguments + ')',))
                    row = cursor.fetchone()
                    checks[name + '_matches_source'] = bool(row) and row[0].replace('\r\n', '\n').strip() == expected.replace('\r\n', '\n').strip()
        return {'read_only': True, 'application_rows_read': False, 'checks': checks,
                'status': 'passed' if all(checks.values()) else 'failed'}
    except Exception as error:
        return {'read_only': True, 'application_rows_read': False, 'checks': checks,
                'status': 'failed', 'error_type': type(error).__name__}


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connect', action='store_true')
    args = parser.parse_args()
    result = run() if args.connect else {'status': 'ready-to-connect', 'read_only': True}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] in ('passed', 'ready-to-connect') else 1)
