"""Actor-specific assignment options; no public account directory."""
from api_v1 import ApiError, BackendUnavailable
from v1_directory import DirectoryService, invalid_query, record_id


class AssignmentOptionsService(DirectoryService):
    def read_options(self, identity, school, args):
        record_id(school)
        if any(key not in {'limit','cursor'} or len(args.getlist(key))!=1 for key in args):
            raise invalid_query()
        limit=args.get('limit','25')
        if not limit.isascii() or not limit.isdecimal() or limit.startswith('0') or len(limit)>3 or not 1<=int(limit)<=100:
            raise invalid_query()
        limit=int(limit)
        binding=[identity.user_id,identity.session_id,'assignment-options',school,limit]
        after_time=after_user=None
        if 'cursor' in args:
            after_time,after_user=self.decode_cursor(args['cursor'],binding,uuid_key=True)
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute('''SELECT public.graphiscan_assignment_options(
                        %s::uuid,%s::uuid,%s::bigint,%s::timestamptz,%s::uuid,%s::integer) AS result''',
                        (identity.user_id,identity.session_id,school,after_time,after_user,limit))
                    result=cursor.fetchone()['result']
            if not isinstance(result,dict) or 'code' not in result or not isinstance(result.get('rows'),list):
                raise BackendUnavailable()
        except Exception:
            raise BackendUnavailable() from None
        if result['code'] is not None:
            statuses={'AUTHENTICATION_REQUIRED':401,'ACCOUNT_UNAVAILABLE':403,'PASSWORD_CHANGE_REQUIRED':403,
                'PRIVACY_ACCEPTANCE_REQUIRED':403,'AGREEMENT_NOT_CONFIGURED':503,'FORBIDDEN':403,'NOT_FOUND':404,'INVALID_QUERY':422}
            code=result['code']
            if code not in statuses:
                raise BackendUnavailable()
            raise ApiError(statuses[code],code,'Assignment choices are unavailable. Refresh your account or check the selected school.')
        rows=result['rows']
        token=None
        if len(rows)>limit:
            rows=rows[:limit]
            token=self.encode_cursor(binding,rows[-1]['created_at'],rows[-1]['data']['user_id'])
        return {'data':[row['data'] for row in rows],'page':{'next_cursor':token}}
