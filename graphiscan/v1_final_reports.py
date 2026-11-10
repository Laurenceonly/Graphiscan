"""Whole-history expert conclusions through scoped PostgreSQL capabilities."""
import json
import re
from api_v1 import ApiError, BackendUnavailable
from v1_directory import record_id
from v1_screening_writes import checked_result, request_key, invalid


def validate_final_report(body, key):
    request_key(key)
    fields = {'summary', 'conclusion', 'next_steps', 'history_fingerprint', 'expected_revision'}
    if not isinstance(body, dict) or body.keys() != fields:
        raise invalid()
    body = dict(body)
    revision = body['expected_revision']
    if type(revision) is not int or not 0 <= revision <= 9223372036854775806:
        raise invalid()
    if not isinstance(body['history_fingerprint'], str) or not re.fullmatch(r'[0-9a-f]{64}', body['history_fingerprint']):
        raise invalid()
    for field in ('summary', 'conclusion', 'next_steps'):
        value = body[field]
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 10000 or '\x00' in value:
            raise invalid()
        body[field] = value.strip()
    return body


class FinalReportService:
    def __init__(self, connect, repository):
        self.connect, self.repository = connect, repository

    def read(self, identity, target):
        record_id(target)
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT public.graphiscan_read_final_report(%s::uuid,%s::uuid,%s::bigint) AS result',
                                   (identity.user_id, identity.session_id, target))
                    row = cursor.fetchone()
        except Exception:
            raise BackendUnavailable() from None
        return self.response(row)

    def finalize(self, identity, target, body, key, request_id):
        record_id(target)
        body = validate_final_report(body, key)
        if self.repository is None:
            raise BackendUnavailable()
        row = self.repository.execute(
            'SELECT public.graphiscan_finalize_report(%s::uuid,%s::uuid,%s::bigint,%s::jsonb,%s::text,%s::uuid) AS result',
            (identity.user_id, identity.session_id, target, json.dumps(body), key, request_id))
        return self.response(row)

    @staticmethod
    def response(row):
        if isinstance(row, dict) and isinstance(row.get('result'), dict) and row['result'].get('code') == 'FINAL_REPORT_NOT_READY':
            raise ApiError(409, 'FINAL_REPORT_NOT_READY', 'Review all completed screenings and mark follow-up as not needed before finalizing.')
        result = checked_result(row)
        if not isinstance(result.get('data'), dict):
            raise BackendUnavailable()
        return {'data': result['data']}
