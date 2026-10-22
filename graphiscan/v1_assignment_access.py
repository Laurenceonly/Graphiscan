"""Explicit actor/candidate/school eligibility with existing administrative scope."""
from uuid import UUID

from api_v1 import ApiError, BackendUnavailable
from v1_account_issuance import _result
from v1_admin_writes import _target_uuid
from v1_directory import record_id


class AssignmentAccessService:
    def __init__(self, reader, writer=None):
        self.reader, self.writer = reader, writer

    def access(self, identity, target, fields, *, write=False, request_id=None):
        expected = {'actor_id', 'school_id'} | ({'expected_revision', 'eligible'} if write else set())
        if not isinstance(fields, dict) or set(fields) != expected:
            raise ApiError(422, 'INVALID_INPUT', 'Choose a school and assigning account.')
        target, actor = _target_uuid(target), _target_uuid(fields['actor_id'])
        school = record_id(fields['school_id'])
        params = (identity.user_id, identity.session_id, target, actor, school)
        if write:
            revision = fields['expected_revision']
            if type(revision) is not int or not 1 <= revision <= 9223372036854775806 or type(fields['eligible']) is not bool:
                raise ApiError(422, 'INVALID_INPUT', 'Supply the current revision and assignment choice.')
            try:
                UUID(request_id)
            except (ValueError, TypeError):
                raise BackendUnavailable() from None
            if self.writer is None:
                raise BackendUnavailable()
            sql = 'SELECT public.graphiscan_set_assignment_access(%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::bigint,%s::bigint,%s::boolean,%s::uuid) AS result'
            params += (revision, fields['eligible'], request_id)
            repository = self.writer
        else:
            sql = 'SELECT public.graphiscan_get_assignment_access(%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::bigint) AS result'
            repository = self.reader
        try:
            row = repository.execute(sql, params)
        except Exception:
            raise BackendUnavailable() from None
        raw = row.get('result') if isinstance(row, dict) else None
        if isinstance(raw, dict) and raw.get('code') == 'INVALID_ASSIGNMENT':
            raise ApiError(422, 'INVALID_ASSIGNMENT', 'The assigning account and candidate must have the required active role and school access.')
        result = _result(row)
        data = result.get('data')
        if (not isinstance(data, dict) or data.get('candidate_id') != target or data.get('actor_id') != actor
                or data.get('school_id') != school or type(data.get('revision')) is not int
                or not all(type(data.get(key)) is bool for key in ('eligible', 'effective', 'can_grant'))):
            raise BackendUnavailable()
        return {'data': data}
