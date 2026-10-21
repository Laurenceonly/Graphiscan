"""Manual fictional-account Auth test. Password is entered at a hidden prompt.

Signs in only graphiscan.test@example.invalid, checks bootstrap/onboarding, then
signs out only that new session. Prints status flags, never credentials/profiles.
No passwords/tokens are written to files. Application database access is read-only.
"""

import getpass
import json
import sys
import warnings
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import requests
from flask import Flask, jsonify
from api_v1 import InvalidSession, install_api_v1, require_access
from v1_backend import SupabasePostgresBackend, backend_from_environment

TEST_EMAIL = "graphiscan.test@example.invalid"


def safe_sign_in_failure(response):
    """Reduce provider failure to fixed codes; never return arbitrary error text."""
    reasons = {"invalid_credentials", "email_not_confirmed", "user_banned",
               "email_provider_disabled", "email_address_invalid", "captcha_failed",
               "over_request_rate_limit", "over_email_send_rate_limit", "validation_failed"}
    status = response.status_code if type(response.status_code) is int else None
    reason = "provider_rejected"
    if status == 429:
        reason = "rate_limited"
    elif status is not None and 300 <= status < 400:
        reason = "unexpected_redirect"
    elif status is not None and status >= 500:
        reason = "auth_service_unavailable"
    try:
        payload = response.json()
        if isinstance(payload, dict):
            code = payload.get("error_code", payload.get("code"))
            if isinstance(code, str) and code in reasons:
                reason = code
            else:
                for field in ("message", "msg", "error_description", "error"):
                    message = payload.get(field)
                    if not isinstance(message, str):
                        continue
                    if message.lower() == "invalid login credentials":
                        reason = "invalid_credentials"
                    elif message.lower() in ("invalid api key", "no api key found in request"):
                        reason = "project_key_rejected"
    except Exception:
        pass
    return {"http_status": status, "reason": reason}


def run_auth_check(password, backend, *, post=None):
    post = requests.post if post is None else post
    report = {"status": "blocked", "checks": [], "auth_session_created": False,
              "application_database_writes": False, "credentials_saved": False}

    def record(name, passed):
        report["checks"].append({"name": name, "status": "pass" if passed else "fail"})
        return passed

    if not record("adapter_configured", isinstance(backend, SupabasePostgresBackend)):
        return report
    if not record("password_supplied", isinstance(password, str) and bool(password)):
        return report
    bearer, client, identity = None, None, None
    headers = {"apikey": backend.verifier.key}
    try:
        response = post(backend.verifier.origin + "/auth/v1/token",
                        params={"grant_type": "password"}, headers=headers,
                        json={"email": TEST_EMAIL, "password": password},
                        timeout=(3.05, 5), allow_redirects=False)
        try:
            if not record("fictional_account_sign_in", response.status_code == 200):
                report["sign_in_failure"] = safe_sign_in_failure(response)
                return report
            payload = response.json()
            if isinstance(payload, dict) and isinstance(payload.get("access_token"), str):
                bearer = payload["access_token"]
                report["auth_session_created"] = bool(bearer)
            if not record("session_response", bool(bearer) and isinstance(payload.get("user"), dict)
                          and payload["user"].get("email", "").lower() == TEST_EMAIL):
                return report
            signed_in_id = payload["user"].get("id")
        finally:
            response.close()

        identity = backend.authenticate(bearer)
        if not record("verified_auth_subject", identity.user_id == signed_in_id):
            return report

        app = Flask("graphiscan-fictional-auth-check")
        install_api_v1(app, backend)
        app.add_url_rule("/api/v1/test-onboarding", "api_v1.test_onboarding",
                         require_access()(lambda: jsonify(data={})))
        client = app.test_client()
        request_headers = {"Authorization": "Bearer " + bearer}
        response = client.get("/api/v1/me", headers=request_headers)
        body = response.get_json() or {}
        profile = body.get("data", {})
        record("verified_session_bootstrap", response.status_code == 200
               and profile.get("user_id") == signed_in_id
               and profile.get("full_name") == "Synthetic Test Admin"
               and profile.get("role") == "admin" and profile.get("account_status") == "active"
               and profile.get("permissions") == [] and profile.get("school_ids") == []
               and response.headers.get("Cache-Control") == "no-store")
        onboarding = profile.get("onboarding", {})
        record("forced_password_state", onboarding.get("must_change_password") is True
               and onboarding.get("next_action") == "change_password")
        denied = client.get("/api/v1/test-onboarding", headers=request_headers)
        denied_body = denied.get_json() or {}
        record("protected_features_blocked", denied.status_code == 403
               and denied_body.get("error", {}).get("code") == "PASSWORD_CHANGE_REQUIRED")
    except Exception:
        record("auth_check_completed", False)  # Never serialize HTTP/DB errors.
    finally:
        if bearer:
            signed_out = False
            try:
                response = post(backend.verifier.origin + "/auth/v1/logout",
                                params={"scope": "local"},
                                headers={**headers, "Authorization": "Bearer " + bearer},
                                timeout=(3.05, 5), allow_redirects=False)
                try:
                    signed_out = response.status_code in (200, 204)
                finally:
                    response.close()
            except Exception:
                pass
            record("local_session_cleanup", signed_out)
            if signed_out and identity is not None:
                try:
                    backend.load_access(identity)
                    record("provider_session_revoked", False)
                except InvalidSession:
                    record("provider_session_revoked", True)
                except Exception:
                    record("provider_session_revoked", False)
            if signed_out and client is not None:
                try:
                    denied = client.get("/api/v1/me", headers={"Authorization": "Bearer " + bearer})
                    record("signed_out_session_denied", denied.status_code == 401
                           and (denied.get_json() or {}).get("error", {}).get("code") == "AUTHENTICATION_REQUIRED")
                except Exception:
                    record("signed_out_session_denied", False)
        report["status"] = "auth-check-passed" if all(c["status"] == "pass" for c in report["checks"]) else "failed"
    return report


def main():
    # No command-line password support and no plaintext fallback for piped input.
    if len(sys.argv) != 1 or not sys.stdin.isatty():
        print(json.dumps({"status": "blocked", "reason": "Use an interactive terminal with no command-line arguments."}))
        return 2
    from dotenv import load_dotenv
    load_dotenv(APP_ROOT / ".env", override=False)
    backend = backend_from_environment()
    if not isinstance(backend, SupabasePostgresBackend):
        print(json.dumps({"status": "blocked", "reason": "Private v1 configuration is incomplete."}))
        return 2
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Fictional Auth account password (hidden): ")
        report = run_auth_check(password, backend)
        password = None
    except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        print(json.dumps({"status": "blocked", "reason": "A hidden interactive password prompt is required."}))
        return 2
    except Exception:
        print(json.dumps({"status": "failed", "reason": "Auth check could not complete; no private details are displayed."}))
        return 1
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "auth-check-passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
