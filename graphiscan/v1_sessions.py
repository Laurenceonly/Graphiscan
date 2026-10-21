"""Session issuance/refresh and durable sign-out. Tokens are response-only secrets."""
from api_v1 import ApiError, BackendUnavailable, InvalidSession, ROLES


def login_fields(body):
    if (not isinstance(body,dict) or set(body)!={'email','password'} or
            not isinstance(body['email'],str) or not isinstance(body['password'],str) or
            not 1<=len(body['password'])<=4096 or len(body['email'])>254 or
            body['email'].count('@')!=1 or any(c.isspace() for c in body['email'].strip())):
        raise ApiError(422,'INVALID_LOGIN','Provide your email and password.')
    email=body['email'].strip().lower()
    if not all(email.split('@')):
        raise ApiError(422,'INVALID_LOGIN','Provide your email and password.')
    return email,body['password']


def refresh_field(body):
    if (not isinstance(body,dict) or set(body)!={'refresh_token'} or
            not isinstance(body['refresh_token'],str) or not 1<=len(body['refresh_token'])<=16384):
        raise ApiError(422,'INVALID_SESSION_REQUEST','Provide the refresh token.')
    return body['refresh_token']


class SessionService:
    def __init__(self,backend,provider,writer):
        self.backend,self.provider,self.writer=backend,provider,writer

    def issue(self,body,*,refresh=False):
        try:
            result=self.provider.call('POST','/token?grant_type='+('refresh_token' if refresh else 'password'),body=body)
        except ApiError as error:
            if error.code=='CURRENT_PASSWORD_INVALID':
                raise ApiError(401,'AUTHENTICATION_REQUIRED','The sign-in details were not accepted.') from None
            raise
        token=result.get('access_token')
        cleanup_token=token if isinstance(token,str) and 0<len(token)<=16384 else None
        try:
            if cleanup_token is None:
                raise BackendUnavailable()
            refresh_token=result.get('refresh_token')
            expires=result.get('expires_in')
            if (not isinstance(refresh_token,str) or not 1<=len(refresh_token)<=16384 or
                    type(expires) is not int or not 1<=expires<=86400 or result.get('token_type')!='bearer'):
                raise BackendUnavailable()
            identity=self.backend.authenticate(token)
            state=self.backend.load_access(identity)
            if state is None or state.user_id!=identity.user_id or state.account_status!='active' or state.role not in ROLES:
                raise ApiError(403,'ACCOUNT_UNAVAILABLE','This account is unavailable.')
            return dict(access_token=token,refresh_token=refresh_token,token_type='bearer',expires_in=expires)
        except Exception:
            if cleanup_token:
                try:self.provider.call('POST','/logout?scope=local',bearer=cleanup_token,expected=204)
                except Exception:pass
            raise

    def login(self,body):
        email,password=login_fields(body)
        return self.issue(dict(email=email,password=password))

    def refresh(self,body):
        return self.issue({'refresh_token':refresh_field(body)},refresh=True)

    def logout(self,identity,bearer,request_id):
        if self.writer is None:
            raise BackendUnavailable()
        row=self.writer.execute('SELECT public.graphiscan_revoke_session(%s::uuid,%s::uuid,%s::uuid) AS ok',
                                (identity.user_id,identity.session_id,request_id))
        if not row or row.get('ok') is not True:
            raise InvalidSession()
        # Revocation is committed before remote sign-out. Provider outage cannot
        # resurrect API access/refresh, and repeating the durable step is harmless.
        try:self.provider.call('POST','/logout?scope=local',bearer=bearer,expected=204)
        except Exception:
            raise ApiError(503,'PROVIDER_SIGNOUT_PENDING','Local access is revoked. Clear this session and sign in again.') from None
