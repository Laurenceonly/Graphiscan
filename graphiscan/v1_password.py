"""Server-only password orchestration. Never persist credentials or retry writes.

An uncertain provider/commit outcome deliberately leaves a durable pending gate.
Recovery requires the operator runbook; an HTTP retry cannot clear that gate.
"""
import re
from uuid import UUID, uuid4

import requests

from api_v1 import ApiError, BackendUnavailable, InvalidSession


def validate_password_change(body):
    keys = {"current_password", "new_password", "confirm_password"}
    if (not isinstance(body, dict) or set(body) != keys or
            any(not isinstance(body[k], str) or not 1 <= len(body[k]) <= 4096 for k in keys)):
        raise ApiError(422, "INVALID_PASSWORD", "Provide all three password fields.")
    current, new = body["current_password"], body["new_password"]
    if (new != body["confirm_password"] or new == current or len(new) < 8 or
            not all(re.search(pattern, new) for pattern in (r"[A-Z]", r"[a-z]", r"[0-9]", r"[^A-Za-z0-9]"))):
        raise ApiError(422, "INVALID_PASSWORD", "Use matching, different passwords with at least eight characters, uppercase, lowercase, a digit and a symbol.")
    return current, new


class SupabasePasswordProvider:
    def __init__(self, verifier, *, http=None):
        self.verifier = verifier
        self.http = http if http is not None else requests

    def call(self, method, path, *, bearer=None, body=None, expected=200):
        headers = {"apikey": self.verifier.key}
        if bearer:
            headers["Authorization"] = "Bearer " + bearer
        try:
            response = self.http.request(method, self.verifier.origin + "/auth/v1" + path,
                                         headers=headers, json=body, timeout=(3.05, 5),
                                         allow_redirects=False)
        except requests.RequestException:
            raise BackendUnavailable() from None
        try:
            if response.status_code != expected:
                if response.status_code == 429:
                    raise ApiError(429, "RATE_LIMITED", "Too many attempts. Wait before trying again.")
                if path == "/token?grant_type=refresh_token" and response.status_code in (400, 401, 403):
                    raise InvalidSession()
                # Only this allowlisted, read-only sign-in failure is actionable.
                if path == "/token?grant_type=password" and response.status_code in (400, 401, 403):
                    try:
                        code = response.json().get("error_code")
                    except (ValueError, AttributeError):
                        code = None
                    if code == "invalid_credentials":
                        raise ApiError(422, "CURRENT_PASSWORD_INVALID", "The current password was not accepted.")
                raise BackendUnavailable()
            if expected == 204:
                return None
            try:
                value = response.json()
            except ValueError:
                raise BackendUnavailable() from None
            if not isinstance(value, dict):
                raise BackendUnavailable()
            return value
        finally:
            response.close()

    def verify_current(self, identity, bearer, password):
        user = self.call("GET", "/user", bearer=bearer)
        if user.get("id") != identity.user_id or not isinstance(user.get("email"), str) or not user["email"]:
            raise BackendUnavailable()
        result = self.call("POST", "/token?grant_type=password",
                           body={"email": user["email"], "password": password})
        token = result.get("access_token")
        if not isinstance(token, str) or not token or len(token) > 16384:
            raise BackendUnavailable()
        # Always clean up the extra sign-in session, including subject mismatch.
        try:
            verified = self.verifier.authenticate(token)
            if verified.user_id != identity.user_id or verified.session_id == identity.session_id:
                raise BackendUnavailable()
        finally:
            self.call("POST", "/logout?scope=local", bearer=token, expected=204)

    def update(self, identity, bearer, current, new):
        user = self.call("PUT", "/user", bearer=bearer,
                         body={"password": new, "current_password": current})
        if user.get("id") != identity.user_id:
            raise BackendUnavailable()

    def sign_out_all(self, bearer):
        self.call("POST", "/logout?scope=global", bearer=bearer, expected=204)


class PostgresPasswordRepository:
    def __init__(self, connect):
        self.connect = connect

    def execute(self, sql, params):
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    row = cursor.fetchone()
            return row
        except Exception:
            raise BackendUnavailable() from None

    def begin(self, identity, operation, request_id):
        row = self.execute("SELECT public.graphiscan_begin_password(%s::uuid,%s::uuid,%s::uuid,%s::uuid) AS ok",
                           (identity.user_id, identity.session_id, operation, request_id))
        if not row or row["ok"] is not True:
            raise InvalidSession()

    def complete(self, identity, operation, request_id):
        row = self.execute("SELECT public.graphiscan_complete_password(%s::uuid,%s::uuid,%s::uuid) AS ok",
                           (identity.user_id, operation, request_id))
        if not row or row["ok"] is not True:
            raise BackendUnavailable()


class PasswordService:
    def __init__(self, provider, repository):
        self.provider, self.repository = provider, repository

    def change(self, identity, bearer, current, new, request_id):
        UUID(request_id)
        self.provider.verify_current(identity, bearer, current)
        operation = str(uuid4())
        # This commit must precede the provider write. Uncertain commit => no PUT.
        self.repository.begin(identity, operation, request_id)
        try:
            self.provider.update(identity, bearer, current, new)
            self.provider.sign_out_all(bearer)
            self.repository.complete(identity, operation, request_id)
        except Exception:
            # Never clear pending based on timeout, provider text or client retry.
            raise ApiError(503, "PASSWORD_CHANGE_RECOVERY_REQUIRED",
                           "Password change could not be confirmed. Contact the administrator before retrying.",
                           "sign_in") from None
