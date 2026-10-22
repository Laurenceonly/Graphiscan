"""Versioned API foundation. No legacy-token fallback or production test identities.

An adapter must verify bearer validity AND durable session revocation, then read
current access state from trusted storage on every request. Missing adapters deny
access. Record endpoints must additionally supply their own current-scope check;
school membership and the /me permission projection are never record authority.
"""

from dataclasses import dataclass
from functools import wraps
from typing import Protocol
from uuid import UUID, uuid4

from flask import Blueprint, g, jsonify, request


ROLES = frozenset({"admin", "researcher", "teacher", "parent", "expert", "guest"})
PERMISSIONS = frozenset({"accounts.manage", "permissions.manage", "schools.manage",
                         "assignments.manage", "audit.read"})


class InvalidSession(Exception):
    """Adapter determined that the bearer/session is invalid, expired or revoked."""


class BackendUnavailable(Exception):
    """Adapter cannot establish trusted current identity/access state."""


class ApiError(Exception):
    def __init__(self, status, code, message, next_action=None):
        self.status, self.code, self.message = status, code, message
        self.next_action = next_action


@dataclass(frozen=True)
class Identity:
    user_id: str
    session_id: str


@dataclass(frozen=True)
class Grant:
    permission: str
    school_id: str | None = None


@dataclass(frozen=True)
class AccessState:
    user_id: str
    full_name: str
    role: str
    account_status: str
    must_change_password: bool
    required_agreement_version: str | None = None
    accepted_agreement_version: str | None = None
    grants: tuple[Grant, ...] = ()
    school_ids: tuple[str, ...] = ()

    def next_action(self):
        if self.must_change_password:
            return "change_password"
        if not self.required_agreement_version:
            return "agreement_unavailable"
        if self.accepted_agreement_version != self.required_agreement_version:
            return "accept_privacy"
        return "ready"


class AccessBackend(Protocol):
    def authenticate(self, bearer: str) -> Identity:
        """Verify issuer/audience/expiry/signature before access-state loading.

        Return only verified UUID subject/session IDs, never client role metadata.
        Raise InvalidSession for denial; BackendUnavailable for service failure.
        Durable session denial may be checked atomically in load_access, which
        the guard must call before accepting this identity for any operation.
        """

    def load_access(self, identity: Identity) -> AccessState | None:
        """Read current profile, grants, memberships and approved agreement state.

        Must also enforce provider session existence, durable app revocation and
        credential-update/security-version session invalidation.
        No cached role claims; missing profile returns None. Reads must be coherent.
        """


class UnavailableBackend:
    def authenticate(self, bearer):
        raise BackendUnavailable()

    def load_access(self, identity):
        raise BackendUnavailable()


def install_api_v1(app, backend: AccessBackend | None = None):
    """Register isolated v1 routes; adapters are supplied by server composition only."""
    app.extensions["graphiscan_v1_backend"] = backend if backend is not None else UnavailableBackend()
    api = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    @api.before_request
    def identify_request():
        # Generate locally: never echo an attacker-controlled header into logs/UI.
        g.v1_request_id = str(uuid4())

    @api.after_request
    def private_response(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = g.v1_request_id
        return response

    @api.errorhandler(ApiError)
    def api_error(error):
        body = {"code": error.code, "message": error.message, "fields": {}}
        if error.next_action:
            body["next_action"] = error.next_action
        return jsonify(error=body, request_id=g.v1_request_id), error.status

    @api.errorhandler(Exception)
    def unexpected_error(error):
        from flask import current_app
        from pathlib import Path
        from traceback import extract_tb
        from werkzeug.exceptions import RequestEntityTooLarge
        if isinstance(error, RequestEntityTooLarge):
            return api_error(ApiError(413, "REQUEST_TOO_LARGE", "The request is too large."))
        # Never log exception text/locals: provider/driver errors can carry secrets.
        frames = [(Path(frame.filename).name, frame.lineno, frame.name)
                  for frame in extract_tb(error.__traceback__)]
        current_app.logger.error('v1_unexpected_error request_id=%s type=%s frames=%s',
                                 g.v1_request_id, type(error).__name__, frames)
        # Do not serialize adapter exceptions (which may include credentials/SQL).
        return api_error(ApiError(500, "INTERNAL_ERROR", "The request could not be completed."))

    @api.get("/health")
    def health():
        # Liveness only. Does not assert DB/Auth/model readiness.
        return jsonify(data={"status": "ok"}, request_id=g.v1_request_id)

    def session_service():
        from flask import current_app
        service = getattr(current_app.extensions["graphiscan_v1_backend"], "session_service", None)
        if service is None:
            raise BackendUnavailable()
        return service

    def session_body():
        request.max_content_length = 24576
        if not request.is_json:
            raise ApiError(400, "INVALID_REQUEST", "A JSON object is required.")
        return request.get_json(silent=True)

    @api.post("/session/login")
    def login_session():
        try:
            return jsonify(data=session_service().login(session_body()),request_id=g.v1_request_id)
        except InvalidSession:
            raise ApiError(401,"AUTHENTICATION_REQUIRED","Sign in to continue.") from None
        except BackendUnavailable:
            raise ApiError(503,"SERVICE_UNAVAILABLE","The service is temporarily unavailable.") from None

    @api.post("/session/refresh")
    def refresh_session():
        try:
            return jsonify(data=session_service().refresh(session_body()),request_id=g.v1_request_id)
        except InvalidSession:
            raise ApiError(401,"AUTHENTICATION_REQUIRED","Sign in to continue.") from None
        except BackendUnavailable:
            raise ApiError(503,"SERVICE_UNAVAILABLE","The service is temporarily unavailable.") from None

    @api.post("/session/logout")
    def logout_session():
        from flask import current_app
        parts=request.headers.get("Authorization", "").split()
        if len(parts)!=2 or parts[0].lower()!='bearer':
            raise ApiError(401,"AUTHENTICATION_REQUIRED","Sign in to continue.")
        backend=current_app.extensions["graphiscan_v1_backend"]
        try:
            identity=backend.authenticate(parts[1])
            UUID(identity.user_id); UUID(identity.session_id)
            # No active-account or onboarding gate: disabled/pending users can leave.
            session_service().logout(identity,parts[1],g.v1_request_id)
            return jsonify(data={"success":True,"next_action":"signed_out"},request_id=g.v1_request_id)
        except InvalidSession:
            raise ApiError(401,"AUTHENTICATION_REQUIRED","Sign in to continue.") from None
        except BackendUnavailable:
            raise ApiError(503,"SERVICE_UNAVAILABLE","The service is temporarily unavailable.") from None

    @api.get("/me")
    @require_access(bootstrap=True)
    def me():
        state = g.v1_access
        return jsonify(data={
            "user_id": state.user_id, "full_name": state.full_name,
            "role": state.role, "account_status": state.account_status,
            "permissions": sorted({grant.permission for grant in state.grants
                                    if grant.permission in PERMISSIONS
                                    and state.role in {"admin", "researcher"}}),
            "school_ids": list(state.school_ids),
            "onboarding": {
                "must_change_password": state.must_change_password,
                "required_agreement_version": state.required_agreement_version,
                "accepted_agreement_version": state.accepted_agreement_version,
                "next_action": state.next_action(),
            },
        }, request_id=g.v1_request_id)

    @api.post("/me/password")
    @require_access(bootstrap=True)
    def change_password():
        from flask import current_app
        from v1_password import validate_password_change
        if request.content_length is not None and request.content_length > 16384:
            raise ApiError(413, "REQUEST_TOO_LARGE", "The request is too large.")
        # Bound chunked requests too, before parsing credentials into memory.
        request.max_content_length = 16384
        if not request.is_json:
            raise ApiError(400, "INVALID_REQUEST", "A JSON object is required.")
        body = request.get_json(silent=True)
        current, new = validate_password_change(body)
        service = getattr(current_app.extensions["graphiscan_v1_backend"], "password_service", None)
        if service is None:
            raise BackendUnavailable()
        service.change(g.v1_identity, request.headers["Authorization"].split()[1],
                       current, new, g.v1_request_id)
        return jsonify(data={"success": True, "next_action": "sign_in"},
                       request_id=g.v1_request_id)

    @api.get("/privacy-agreement")
    @require_access(bootstrap=True)
    def privacy_agreement():
        from flask import current_app
        from v1_privacy import password_gate
        password_gate(g.v1_access)
        service = getattr(current_app.extensions["graphiscan_v1_backend"], "privacy_service", None)
        if service is None:
            raise BackendUnavailable()
        return jsonify(data=service.get_agreement(g.v1_identity), request_id=g.v1_request_id)

    @api.post("/me/privacy-acceptance")
    @require_access(bootstrap=True)
    def accept_privacy():
        from flask import current_app
        from v1_privacy import password_gate, validate_acceptance
        password_gate(g.v1_access)
        request.max_content_length = 4096
        if not request.is_json:
            raise ApiError(400, "INVALID_REQUEST", "A JSON object is required.")
        version = validate_acceptance(request.get_json(silent=True))
        service = getattr(current_app.extensions["graphiscan_v1_backend"], "privacy_service", None)
        if service is None:
            raise BackendUnavailable()
        return jsonify(data=service.accept(g.v1_identity, version, g.v1_request_id), request_id=g.v1_request_id)

    def read_directory(resource, target=None):
        from flask import current_app
        service = getattr(current_app.extensions['graphiscan_v1_backend'], 'directory_service', None)
        if service is None:
            raise BackendUnavailable()
        result = service.read(g.v1_identity, resource, request.args, target)
        return jsonify(**result, request_id=g.v1_request_id)

    @api.get('/schools')
    @require_access(roles={'admin', 'researcher', 'teacher', 'parent', 'expert'})
    def list_schools():
        return read_directory('schools')

    @api.get('/students')
    @require_access(roles={'admin', 'researcher', 'teacher', 'parent', 'expert'})
    def list_students():
        return read_directory('students')

    @api.get('/students/<student_id>')
    @require_access(roles={'admin', 'researcher', 'teacher', 'parent', 'expert'})
    def get_student(student_id):
        return read_directory('student', student_id)

    def read_admin(resource):
        from flask import current_app
        service = getattr(current_app.extensions['graphiscan_v1_backend'], 'admin_read_service', None)
        if service is None:
            raise BackendUnavailable()
        return jsonify(**service.read(g.v1_identity, resource, request.args), request_id=g.v1_request_id)

    @api.get('/accounts')
    @require_access(roles={'admin', 'researcher'}, permission='accounts.manage')
    def list_admin_accounts():
        return read_admin('accounts')

    @api.get('/audit-logs')
    @require_access(roles={'admin', 'researcher'}, permission='audit.read')
    def list_admin_audit_logs():
        return read_admin('audit')

    def admin_lifecycle():
        from flask import current_app
        service = getattr(current_app.extensions['graphiscan_v1_backend'], 'admin_lifecycle_service', None)
        if service is None:
            raise BackendUnavailable()
        return service

    @api.get('/accounts/<user_id>')
    @require_access(roles={'admin', 'researcher'}, permission='accounts.manage')
    def get_admin_account(user_id):
        if request.args:
            raise ApiError(400, 'INVALID_REQUEST', 'Do not supply query parameters.')
        return jsonify(**admin_lifecycle().detail(g.v1_identity, user_id), request_id=g.v1_request_id)

    @api.get('/account-operations/<operation_id>')
    @require_access(roles={'admin', 'researcher'}, permission='accounts.manage')
    def get_admin_account_operation(operation_id):
        if request.args:
            raise ApiError(400, 'INVALID_REQUEST', 'Do not supply query parameters.')
        return jsonify(**admin_lifecycle().status(g.v1_identity, operation_id), request_id=g.v1_request_id)

    def perform_admin_account_operation(user_id, action):
        request.max_content_length = 8192
        if request.args or not request.is_json:
            raise ApiError(400, 'INVALID_REQUEST', 'Supply a JSON object without query parameters.')
        bearer = request.headers['Authorization'].split()[1]
        return jsonify(**admin_lifecycle().perform(g.v1_identity, bearer, user_id, action,
            request.get_json(silent=True), request.headers.get('Idempotency-Key'), g.v1_request_id), request_id=g.v1_request_id)

    @api.post('/accounts/<user_id>/temporary-password')
    @require_access(roles={'admin', 'researcher'}, permission='accounts.manage')
    def reset_admin_account_password(user_id):
        return perform_admin_account_operation(user_id, 'reset_password')

    @api.delete('/accounts/<user_id>')
    @require_access(roles={'admin', 'researcher'}, permission='accounts.manage')
    def delete_admin_account(user_id):
        return perform_admin_account_operation(user_id, 'delete')

    @api.post('/accounts')
    @require_access(roles={'admin', 'researcher'}, permission='accounts.manage')
    def create_admin_account():
        from flask import current_app
        request.max_content_length = 8192
        if request.args or not request.is_json:
            raise ApiError(400, 'INVALID_REQUEST', 'Supply a JSON object without query parameters.')
        service = getattr(current_app.extensions['graphiscan_v1_backend'], 'account_issuance_service', None)
        if service is None:
            raise ApiError(503, 'ACCOUNT_CREATION_UNAVAILABLE', 'Account creation is not configured. Contact the system operator.')
        return jsonify(**service.create(g.v1_identity, request.get_json(silent=True),
            request.headers.get('Idempotency-Key'), g.v1_request_id), request_id=g.v1_request_id), 201

    @api.patch('/accounts/<user_id>')
    @require_access(roles={'admin', 'researcher'}, permission='accounts.manage')
    def update_admin_account(user_id):
        from flask import current_app
        request.max_content_length = 32768
        if request.args or not request.is_json:
            raise ApiError(400, 'INVALID_REQUEST', 'Supply a JSON object without query parameters.')
        service = getattr(current_app.extensions['graphiscan_v1_backend'], 'admin_write_service', None)
        if service is None:
            raise BackendUnavailable()
        return jsonify(**service.update(g.v1_identity, user_id, request.get_json(silent=True),
            g.v1_request_id), request_id=g.v1_request_id)

    def write_directory(operation, target=None):
        from flask import current_app
        request.max_content_length = 8192
        if request.args or not request.is_json:
            raise ApiError(400, 'INVALID_REQUEST', 'Supply a JSON object without query parameters.')
        service = getattr(current_app.extensions['graphiscan_v1_backend'], 'directory_write_service', None)
        if service is None:
            raise BackendUnavailable()
        result = service.write(g.v1_identity, operation, target, request.get_json(silent=True),
                               request.headers.get('Idempotency-Key'), g.v1_request_id)
        response = jsonify(**result, request_id=g.v1_request_id)
        if operation.endswith('.create'):
            resource = 'schools' if operation.startswith('schools.') else 'students'
            identifier = 'school_id' if resource == 'schools' else 'student_id'
            response.status_code = 201
            response.headers['Location'] = '/api/v1/' + resource + '/' + result['data'][identifier]
        return response

    @api.post('/schools')
    @require_access(roles={'admin', 'researcher'})
    def create_school():
        return write_directory('schools.create')

    @api.patch('/schools/<school_id>')
    @require_access(roles={'admin', 'researcher'})
    def update_school(school_id):
        return write_directory('schools.update', school_id)

    @api.post('/students')
    @require_access(roles={'admin', 'researcher', 'teacher'})
    def create_student():
        return write_directory('students.create')

    @api.patch('/students/<student_id>')
    @require_access(roles={'admin', 'researcher', 'teacher'})
    def update_student(student_id):
        return write_directory('students.update', student_id)

    @api.get('/schools/<school_id>/assignment-options')
    @require_access(roles={'admin','researcher','teacher'})
    def assignment_options(school_id):
        from flask import current_app
        service=getattr(current_app.extensions['graphiscan_v1_backend'],'assignment_options_service',None)
        if service is None:
            raise BackendUnavailable()
        return jsonify(**service.read_options(g.v1_identity,school_id,request.args),request_id=g.v1_request_id)

    def read_screenings(resource, target=None):
        from flask import current_app
        service=getattr(current_app.extensions['graphiscan_v1_backend'],'screening_read_service',None)
        if service is None:
            raise BackendUnavailable()
        return jsonify(**service.read(g.v1_identity,resource,request.args,target),request_id=g.v1_request_id)

    @api.get('/screenings')
    @require_access(roles={'admin','researcher','teacher','parent','expert'})
    def list_screenings():
        return read_screenings('screenings')

    @api.get('/screenings/<result_id>')
    @require_access(roles={'admin','researcher','teacher','parent','expert'})
    def get_screening(result_id):
        return read_screenings('screening',result_id)

    @api.get('/students/<student_id>/history')
    @require_access(roles={'admin','researcher','teacher','parent','expert'})
    def screening_history(student_id):
        return read_screenings('history',student_id)

    @api.get('/reports/<report_id>')
    @require_access(roles={'admin','researcher','teacher','parent','expert'})
    def get_report(report_id):
        return read_screenings('report',report_id)

    def write_screening(operation, target):
        from flask import current_app
        request.max_content_length=32768
        if request.args or not request.is_json:
            raise ApiError(400,'INVALID_REQUEST','Supply a JSON object without query parameters.')
        service=getattr(current_app.extensions['graphiscan_v1_backend'],'screening_write_service',None)
        if service is None:raise BackendUnavailable()
        return jsonify(**service.write(g.v1_identity,operation,target,request.get_json(silent=True),
            request.headers.get('Idempotency-Key'),g.v1_request_id),request_id=g.v1_request_id)

    @api.patch('/screenings/<result_id>/review')
    @require_access(roles={'expert'})
    def review_screening(result_id):return write_screening('review',result_id)

    @api.patch('/screenings/<result_id>/expert-assignment')
    @require_access(roles={'admin','researcher'})
    def assign_screening(result_id):return write_screening('assignment',result_id)

    def upload_service():
        from flask import current_app
        service=getattr(current_app.extensions['graphiscan_v1_backend'],'screening_upload_service',None)
        if service is None:raise BackendUnavailable()
        return service

    @api.get('/models')
    @require_access(roles={'admin','researcher','teacher','parent','expert'})
    def list_models():return jsonify(**upload_service().catalogue(g.v1_identity,request.args),request_id=g.v1_request_id)

    @api.post('/screenings')
    @require_access(roles={'teacher'})
    def create_screening():
        from v1_uploads import MAX_BYTES
        from flask import current_app
        from werkzeug.datastructures import MultiDict
        request.max_content_length=MAX_BYTES+65536
        request.max_form_memory_size=16384
        if request.args or request.mimetype!='multipart/form-data':
            raise ApiError(400,'INVALID_REQUEST','Supply a multipart handwriting upload without query parameters.')
        result_id=upload_service().upload(g.v1_identity,request.form,request.files,
            request.headers.get('Idempotency-Key'),g.v1_request_id)
        reader=getattr(current_app.extensions['graphiscan_v1_backend'],'screening_read_service',None)
        if reader is None:raise BackendUnavailable()
        response=jsonify(**reader.read(g.v1_identity,'screening',MultiDict(),result_id),request_id=g.v1_request_id)
        response.status_code=201;response.headers['Location']='/api/v1/screenings/'+result_id
        return response

    @api.get('/screening-requests/<idempotency_key>')
    @require_access(roles={'teacher'})
    def get_screening_request(idempotency_key):
        if request.args:raise ApiError(422,'INVALID_QUERY','No query parameters are supported.')
        return jsonify(**upload_service().request_state(g.v1_identity,idempotency_key),request_id=g.v1_request_id)

    @api.get('/screenings/<result_id>/image')
    @require_access(roles={'admin','researcher','teacher','parent','expert'})
    def screening_image(result_id):
        from flask import make_response
        if request.args:raise ApiError(422,'INVALID_QUERY','No query parameters are supported.')
        data,content_type=upload_service().image(g.v1_identity,result_id)
        response=make_response(data)
        response.headers['Content-Type']=content_type
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Content-Disposition']='inline; filename="handwriting.png"'
        return response

    app.register_blueprint(api)


def require_access(*, bootstrap=False, roles=None, permission=None,
                   school_scope=None, record_scope=None):
    """Check trusted access on every request, before entering the handler.

    school_scope(**route_args) returns the target school ID, or None for a global
    operation (requiring a global grant). record_scope(state, **route_args) must
    re-read current ownership/assignment/release and return True to permit access.
    Missing and inaccessible records share a 404. Callbacks must fail closed.
    Bootstrap bypasses onboarding only, never account availability.
    """
    if permission is not None and permission not in PERMISSIONS:
        raise ValueError("Unknown permission")
    if bootstrap and any((roles is not None, permission is not None,
                          school_scope is not None, record_scope is not None)):
        raise ValueError("Bootstrap cannot be combined with resource access")

    def decorate(handler):
        @wraps(handler)
        def wrapped(*args, **kwargs):
            from flask import current_app
            backend = current_app.extensions["graphiscan_v1_backend"]
            parts = request.headers.get("Authorization", "").split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise ApiError(401, "AUTHENTICATION_REQUIRED", "Sign in to continue.")
            try:
                identity = backend.authenticate(parts[1])
                # An incomplete adapter response must never establish a session.
                UUID(identity.user_id)
                UUID(identity.session_id)
                state = backend.load_access(identity)
                if state is None or state.user_id != identity.user_id or state.account_status != "active" or state.role not in ROLES:
                    raise ApiError(403, "ACCOUNT_UNAVAILABLE", "This account is unavailable.")
                g.v1_identity, g.v1_access = identity, state
                if not bootstrap:
                    action = state.next_action()
                    if action == "change_password":
                        raise ApiError(403, "PASSWORD_CHANGE_REQUIRED", "Change your password to continue.", action)
                    if action == "agreement_unavailable":
                        raise ApiError(503, "AGREEMENT_NOT_CONFIGURED", "The privacy agreement is unavailable.", action)
                    if action == "accept_privacy":
                        raise ApiError(403, "PRIVACY_ACCEPTANCE_REQUIRED", "Read and accept the current privacy agreement to continue.", action)
                    if roles is not None and state.role not in roles:
                        raise ApiError(403, "FORBIDDEN", "You do not have access to this feature.")
                    if permission is not None:
                        school = school_scope(**kwargs) if school_scope else None
                        allowed = state.role in {"admin", "researcher"} and any(
                            grant.permission == permission and
                            (grant.school_id is None or (school is not None and grant.school_id == school))
                            for grant in state.grants)
                        if not allowed:
                            raise ApiError(403, "FORBIDDEN", "You do not have access to this feature.")
                    if record_scope is not None and record_scope(state, **kwargs) is not True:
                        raise ApiError(404, "NOT_FOUND", "The requested record was not found.")
                return handler(*args, **kwargs)
            except InvalidSession:
                raise ApiError(401, "AUTHENTICATION_REQUIRED", "Sign in to continue.") from None
            except BackendUnavailable:
                raise ApiError(503, "SERVICE_UNAVAILABLE", "The service is temporarily unavailable.") from None
        return wrapped
    return decorate
