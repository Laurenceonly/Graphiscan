"""Human review/assignment writes through bounded transactional capabilities."""
import json
import re
from uuid import UUID
from api_v1 import ApiError, BackendUnavailable
from v1_directory import record_id

ERRORS={
    'AUTHENTICATION_REQUIRED':(401,'Sign in to continue.',None),
    'ACCOUNT_UNAVAILABLE':(403,'This account is unavailable.',None),
    'PASSWORD_CHANGE_REQUIRED':(403,'Change your password to continue.','change_password'),
    'AGREEMENT_NOT_CONFIGURED':(503,'The privacy agreement is unavailable.','agreement_unavailable'),
    'PRIVACY_ACCEPTANCE_REQUIRED':(403,'Read and accept the current privacy agreement to continue.','accept_privacy'),
    'FORBIDDEN':(403,'You do not have access to this operation.',None),
    'NOT_FOUND':(404,'The requested record was not found.',None),
    'INVALID_INPUT':(422,'Check the submitted screening fields.',None),
    'INVALID_ASSIGNMENT':(422,'Choose an eligible active expert for this school.',None),
    'REVISION_CONFLICT':(409,'This record changed. Reload it before saving again.',None),
    'IDEMPOTENCY_CONFLICT':(409,'Keep the original request key and payload together.',None),
    'REQUEST_IN_PROGRESS':(409,'This request is still processing. Check its status before submitting again.',None),
    'MODEL_UNAVAILABLE':(503,'The selected screening model is unavailable.',None),
    'STORAGE_UNAVAILABLE':(503,'Private image storage is unavailable.',None),
}
def checked_result(row):
    result=row.get('result') if isinstance(row,dict) else None
    if not isinstance(result,dict) or 'code' not in result:raise BackendUnavailable()
    code=result['code']
    if code is not None:
        if code not in ERRORS:raise BackendUnavailable()
        status,message,action=ERRORS[code]
        raise ApiError(status,code,message,action)
    return result

def request_key(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,128}',value):
        raise ApiError(422,'IDEMPOTENCY_KEY_REQUIRED','Provide a valid Idempotency-Key and retain it with this submission.')
    return value

def invalid():return ApiError(422,'INVALID_INPUT','Check the submitted screening fields.')
def validate_write(operation,body,key=None):
    if not isinstance(body,dict):raise invalid()
    body=dict(body)
    revision=body.get('expected_revision')
    if type(revision) is not int or not 1<=revision<=9223372036854775806:raise invalid()
    if operation=='review':
        request_key(key)
        if not {'status','remarks','follow_up_needed','expected_revision'}<=body.keys() or body.keys()-{'status','remarks','expert_recommendation','follow_up_needed','expected_revision'}:raise invalid()
        if body['status'] not in ('Validated','Flagged') or type(body['follow_up_needed']) is not bool:raise invalid()
        for field in ('remarks','expert_recommendation'):
            value=body.get(field)
            if field=='expert_recommendation' and value is None:continue
            if not isinstance(value,str) or not 1<=len(value.strip())<=10000 or '\x00' in value:raise invalid()
            body[field]=value.strip()
    elif operation=='assignment':
        if body.keys()!={'assigned_expert_id','expected_revision'}:raise invalid()
        value=body['assigned_expert_id']
        if value is not None:
            try:
                if not isinstance(value,str) or not re.fullmatch(r'[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',value):raise ValueError()
                body['assigned_expert_id']=str(UUID(value))
            except (TypeError,ValueError):raise invalid() from None
    else:raise invalid()
    return body

class ScreeningWriteService:
    def __init__(self,repository):self.repository=repository
    def write(self,identity,operation,target,body,key,request_id):
        record_id(target);body=validate_write(operation,body,key)
        if self.repository is None:raise BackendUnavailable()
        params=(identity.user_id,identity.session_id,target,json.dumps(body))
        if operation=='review':
            sql='SELECT public.graphiscan_write_review(%s::uuid,%s::uuid,%s::bigint,%s::jsonb,%s::text,%s::uuid) AS result'
            params+=(key,request_id)
        else:
            sql='SELECT public.graphiscan_assign_expert(%s::uuid,%s::uuid,%s::bigint,%s::jsonb,%s::uuid) AS result'
            params+=(request_id,)
        result=checked_result(self.repository.execute(sql,params))
        if not isinstance(result.get('data'),dict):raise BackendUnavailable()
        return {'data':result['data']}
