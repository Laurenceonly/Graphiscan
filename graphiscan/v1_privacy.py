"""Versioned notice reads and atomic acceptance; no client-supplied consent time."""
from api_v1 import ApiError, BackendUnavailable, InvalidSession


AGREEMENT_SQL = """SELECT a.version,a.title,a.content,a.published_at FROM public.privacy_agreements a
    CROSS JOIN (SELECT %s::text AS subject_id) identity
    WHERE a.is_current AND a.approved_by IS NOT NULL AND a.approved_at <= statement_timestamp()
      AND a.published_at <= statement_timestamp()
      AND a.content_sha256=encode(sha256(convert_to(a.content,'UTF8')),'hex')
      AND ((to_jsonb(a)->>'test_subject_id') IS NULL OR (to_jsonb(a)->>'test_subject_id')=identity.subject_id)
      AND ((to_jsonb(a)->>'test_subject_ids') IS NULL
           OR (to_jsonb(a)->'test_subject_ids') @> jsonb_build_array(identity.subject_id))"""


def password_gate(state):
    if state.must_change_password:
        raise ApiError(403, 'PASSWORD_CHANGE_REQUIRED', 'Change your password to continue.', 'change_password')


def agreement_unavailable():
    return ApiError(503, 'AGREEMENT_NOT_CONFIGURED', 'The privacy agreement is unavailable.', 'agreement_unavailable')


def validate_acceptance(body):
    if (not isinstance(body, dict) or set(body) != {'agreement_version', 'accepted'} or
            body['accepted'] is not True or not isinstance(body['agreement_version'], str) or
            not body['agreement_version'].strip() or len(body['agreement_version']) > 256):
        raise ApiError(422, 'INVALID_ACCEPTANCE', 'Read the notice and explicitly accept its current version.')
    return body['agreement_version']


def timestamp(value):
    # psycopg returns timezone-aware datetimes. Do not silently emit naive time.
    if value is None or value.tzinfo is None or value.utcoffset() is None:
        raise BackendUnavailable()
    return value.isoformat()


class PrivacyService:
    def __init__(self, read_connect, writer_repository=None):
        self.read_connect, self.writer = read_connect, writer_repository

    def get_agreement(self, identity):
        try:
            with self.read_connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(AGREEMENT_SQL, (identity.user_id,))
                    row = cursor.fetchone()
            if row is None:
                raise agreement_unavailable()
            return {key: (timestamp(row[key]) if key == 'published_at' else row[key])
                    for key in ('version','title','content','published_at')}
        except ApiError:
            raise
        except Exception:
            raise BackendUnavailable() from None

    def accept(self, identity, version, request_id):
        if self.writer is None:
            raise BackendUnavailable()
        row = self.writer.execute('SELECT * FROM public.graphiscan_accept_privacy(%s::uuid,%s::uuid,%s,%s::uuid)',
                                  (identity.user_id,identity.session_id,version,request_id))
        if not row:
            raise BackendUnavailable()
        outcome = row.get('outcome')
        if outcome == 'invalid_session':
            raise InvalidSession()
        if outcome == 'account_unavailable':
            raise ApiError(403, 'ACCOUNT_UNAVAILABLE', 'This account is unavailable.')
        if outcome == 'password_required':
            raise ApiError(403, 'PASSWORD_CHANGE_REQUIRED', 'Change your password to continue.', 'change_password')
        if outcome == 'agreement_unavailable':
            raise agreement_unavailable()
        if outcome == 'agreement_changed':
            raise ApiError(409, 'AGREEMENT_CHANGED', 'The notice changed. Read its current version before accepting.', 'accept_privacy')
        if outcome != 'accepted' or row.get('agreement_version') != version:
            raise BackendUnavailable()
        return {'agreement_version': version, 'accepted_at': timestamp(row.get('accepted_at'))}
