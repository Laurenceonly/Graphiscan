"""Current-scope hosted screening reads; no legacy IDs/tokens or storage paths."""
import json
import re
from datetime import datetime, timezone

from api_v1 import ApiError, BackendUnavailable
from v1_directory import DirectoryService, invalid_query, record_id


def date_filter(value):
    try:
        if len(value) > 40 or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T.+', value):
            raise ValueError()
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError()
        return stamp.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError):
        raise invalid_query() from None


class ScreeningReadService(DirectoryService):
    def read(self, identity, resource, args, target=None):
        filters_allowed = {'student_id','school_id','grade_level','validation_status','model_id','task_type','from','to'}
        allowed = {'limit','cursor'} | filters_allowed if resource == 'screenings' else {'limit','cursor','order'} if resource == 'history' else set()
        if resource not in {'screenings','screening','history','report'} or any(k not in allowed or len(args.getlist(k)) != 1 for k in args):
            raise invalid_query()
        if resource != 'screenings':
            record_id(target)
        limit = args.get('limit','25')
        if not re.fullmatch(r'[1-9][0-9]{0,2}',limit) or int(limit) > 100:
            raise invalid_query()
        limit = int(limit)
        order = args.get('order','newest')
        if order not in {'newest','oldest'}:
            raise invalid_query()
        filters = {k:args[k] for k in filters_allowed if k in args}
        for key in ('student_id','school_id','model_id'):
            if key in filters:
                record_id(filters[key])
        for key, values in [('grade_level',{'1','2','3'}),('validation_status',{'Pending','Validated','Flagged'}),('task_type',{'binary','three_class'})]:
            if key in filters and filters[key] not in values:
                raise invalid_query()
        for key in ('from','to'):
            if key in filters:
                filters[key] = date_filter(filters[key])
        if 'from' in filters and 'to' in filters and filters['from'] > filters['to']:
            raise invalid_query()
        binding = [identity.user_id,identity.session_id,resource,target,filters,order,limit]
        after_time,after_id = self.decode_cursor(args['cursor'],binding) if 'cursor' in args else (None,None)
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute('''SELECT public.graphiscan_read_screenings(
                        %s::uuid,%s::uuid,%s::text,%s::jsonb,%s::timestamptz,%s::bigint,
                        %s::integer,%s::bigint,%s::boolean) AS result''',
                        (identity.user_id,identity.session_id,resource,json.dumps(filters),after_time,after_id,limit,target,order=='oldest'))
                    result = cursor.fetchone()['result']
            if not isinstance(result,dict) or not isinstance(result.get('rows'),list):
                raise BackendUnavailable()
        except Exception:
            raise BackendUnavailable() from None
        errors = {
            'AUTHENTICATION_REQUIRED':(401,'Sign in to continue.',None),
            'ACCOUNT_UNAVAILABLE':(403,'This account is unavailable.',None),
            'PASSWORD_CHANGE_REQUIRED':(403,'Change your password to continue.','change_password'),
            'AGREEMENT_NOT_CONFIGURED':(503,'The privacy agreement is unavailable.','agreement_unavailable'),
            'PRIVACY_ACCEPTANCE_REQUIRED':(403,'Read and accept the current privacy agreement to continue.','accept_privacy'),
            'FORBIDDEN':(403,'You do not have access to this feature.',None),
            'INVALID_QUERY':(422,'Check the list filters or start a new list.',None)}
        code = result.get('code')
        if code is not None:
            if code not in errors:
                raise BackendUnavailable()
            status,message,action = errors[code]
            raise ApiError(status,code,message,action)
        rows = result['rows']
        if resource in {'screening','report'}:
            if not rows:
                raise ApiError(404,'NOT_FOUND','The requested record was not found.')
            return {'data':rows[0]}
        if resource == 'history' and result.get('found') is not True:
            raise ApiError(404,'NOT_FOUND','The requested record was not found.')
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = self.encode_cursor(binding,rows[-1]['date_generated'],rows[-1]['result_id'])
        return {'data':rows,'page':{'next_cursor':next_cursor}}
