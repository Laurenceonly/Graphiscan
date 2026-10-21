"""Fictional login checker tests: no real Auth/DB calls, credentials or sessions."""

import io
import json
import unittest
from dataclasses import replace
from unittest.mock import Mock, patch

import requests
from api_v1 import AccessState, Identity, InvalidSession, UnavailableBackend
from tools.check_v1_auth import TEST_EMAIL, main, run_auth_check, safe_sign_in_failure
from v1_backend import SupabasePostgresBackend

USER = "00000000-0000-4000-8000-000000000001"
SESSION = "00000000-0000-4000-8000-000000000002"


class AuthCheckTests(unittest.TestCase):
    def setUp(self):
        self.active = False
        self.logout_ok = True
        self.drop_session = True
        self.login_status = 200
        self.payload = {"access_token": "synthetic-access-private", "refresh_token": "synthetic-refresh-private",
                        "user": {"id": USER, "email": TEST_EMAIL}}
        self.state = AccessState(USER, "Synthetic Test Admin", "admin", "active", True)
        self.verifier = Mock(origin="https://synthetic-project.example.invalid", key="sb_publishable_synthetic_private")

        def authenticate(bearer):
            if not self.active:
                raise InvalidSession()
            return Identity(USER, SESSION)

        def load_access(identity):
            if not self.active:
                raise InvalidSession()
            return self.state

        self.verifier.authenticate.side_effect = authenticate
        self.repo = Mock()
        self.repo.load_access.side_effect = load_access
        self.backend = SupabasePostgresBackend(self.verifier, self.repo)

        def post(url, **kwargs):
            if url.endswith("/token"):
                response = Mock(status_code=self.login_status)
                response.json.return_value = self.payload
                self.active = self.login_status == 200
                return response
            if url.endswith("/logout"):
                if self.logout_ok and self.drop_session:
                    self.active = False
                return Mock(status_code=204 if self.logout_ok else 503)
            raise AssertionError("Unexpected endpoint")

        self.post = Mock(side_effect=post)

    def run_check(self):
        report = run_auth_check("synthetic-password-private", self.backend, post=self.post)
        output = json.dumps(report)
        for private in ("synthetic-password-private", "synthetic-access-private", "synthetic-refresh-private", USER, SESSION, "Synthetic Test Admin"):
            self.assertNotIn(private, output)
        return report

    def test_success_checks_bootstrap_gates_local_logout_and_durable_denial(self):
        report = self.run_check()
        self.assertEqual(report["status"], "auth-check-passed")
        self.assertFalse(self.active)
        self.assertTrue(report["auth_session_created"])
        self.assertFalse(report["application_database_writes"])
        self.assertFalse(report["credentials_saved"])
        self.assertTrue(all(c["status"] == "pass" for c in report["checks"]))
        self.assertEqual(self.post.call_args_list[0].kwargs["params"], {"grant_type": "password"})
        self.assertEqual(self.post.call_args_list[0].kwargs["json"]["email"], TEST_EMAIL)
        self.assertEqual(self.post.call_args_list[1].kwargs["params"], {"scope": "local"})
        for call in self.post.call_args_list:
            self.assertFalse(call.kwargs["allow_redirects"])
            self.assertEqual(call.kwargs["timeout"], (3.05, 5))

    def test_bad_password_or_redirect_does_not_retry_or_attempt_logout(self):
        for status in (400, 401, 403, 302, 429, 503):
            self.post.reset_mock()
            self.login_status = status
            self.assertEqual(self.run_check()["status"], "failed")
            self.assertEqual(self.post.call_count, 1)

    def test_provider_error_codes_are_allowlisted_and_free_text_is_redacted(self):
        for code in ("invalid_credentials", "email_not_confirmed", "email_provider_disabled", "user_banned"):
            response = Mock(status_code=400)
            response.json.return_value = {"error_code": code, "msg": "synthetic-password-private"}
            self.assertEqual(safe_sign_in_failure(response), {"http_status": 400, "reason": code})
        response.json.return_value = {"error_code": "synthetic-password-private", "message": "synthetic-access-private"}
        self.assertEqual(safe_sign_in_failure(response), {"http_status": 400, "reason": "provider_rejected"})

    def test_sign_in_failure_report_contains_safe_reason_without_new_attempt(self):
        self.login_status = 400
        self.payload = {"error_code": "invalid_credentials", "msg": "synthetic-password-private"}
        report = self.run_check()
        self.assertEqual(report["sign_in_failure"], {"http_status": 400, "reason": "invalid_credentials"})
        self.assertEqual(self.post.call_count, 1)
        self.assertFalse(report["auth_session_created"])

    def test_known_gateway_messages_and_non_json_failures_are_sanitized(self):
        response = Mock(status_code=401)
        response.json.return_value = {"message": "Invalid API key"}
        self.assertEqual(safe_sign_in_failure(response)["reason"], "project_key_rejected")
        response.json.return_value = {"error_description": "Invalid login credentials"}
        self.assertEqual(safe_sign_in_failure(response)["reason"], "invalid_credentials")
        for status, expected in ((302, "unexpected_redirect"), (429, "rate_limited"), (503, "auth_service_unavailable")):
            response.status_code = status
            response.json.side_effect = ValueError("synthetic-password-private")
            self.assertEqual(safe_sign_in_failure(response), {"http_status": status, "reason": expected})

    def test_missing_configuration_and_empty_password_never_call_provider(self):
        report = run_auth_check("synthetic", UnavailableBackend(), post=self.post)
        self.assertEqual(report["status"], "blocked")
        report = run_auth_check("", self.backend, post=self.post)
        self.assertEqual(report["status"], "blocked")
        self.post.assert_not_called()

    def test_login_exception_is_redacted(self):
        self.post.side_effect = requests.Timeout("synthetic-password-private synthetic-access-private")
        report = self.run_check()
        self.assertEqual(report["status"], "failed")

    def test_wrong_user_or_invalid_response_still_cleans_issued_session(self):
        self.payload["user"]["email"] = "other@example.invalid"
        self.assertEqual(self.run_check()["status"], "failed")
        self.assertEqual(self.post.call_count, 2)
        self.assertFalse(self.active)

    def test_verifier_failure_after_login_still_attempts_cleanup(self):
        self.verifier.authenticate.side_effect = RuntimeError("synthetic-password-private")
        self.assertEqual(self.run_check()["status"], "failed")
        self.assertFalse(self.active)

    def test_missing_profile_and_onboarding_bypass_fail_and_cleanup(self):
        original = self.state
        for state in (None, replace(original, must_change_password=False), replace(original, account_status="disabled")):
            self.state = state
            self.assertEqual(self.run_check()["status"], "failed")
            self.assertFalse(self.active)

    def test_logout_failure_and_still_valid_session_are_not_reported_as_pass(self):
        self.logout_ok = False
        self.assertEqual(self.run_check()["status"], "failed")
        self.logout_ok = True
        self.drop_session = False
        report = self.run_check()
        self.assertEqual(report["status"], "failed")
        self.assertIn({"name": "provider_session_revoked", "status": "fail"}, report["checks"])

    def test_noninteractive_or_argument_input_is_blocked_before_password_prompt(self):
        for args, interactive in ((["checker"], False), (["checker", "synthetic-password-private"], True)):
            output = io.StringIO()
            with patch("sys.argv", args), patch("sys.stdin.isatty", return_value=interactive), patch("getpass.getpass") as prompt, patch("sys.stdout", output):
                self.assertEqual(main(), 2)
                prompt.assert_not_called()
            self.assertNotIn("synthetic-password-private", output.getvalue())


if __name__ == "__main__":
    unittest.main()
