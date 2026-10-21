"""Synthetic runtime checks; no config, database, JWT service or student data."""

import unittest
from dataclasses import replace
from uuid import UUID

from flask import Flask, jsonify

from api_v1 import (AccessState, BackendUnavailable, Grant, Identity,
                    InvalidSession, install_api_v1, require_access)


USER = "00000000-0000-4000-8000-000000000001"
SESSION = "00000000-0000-4000-8000-000000000002"


class SyntheticBackend:
    def __init__(self):
        self.state = AccessState(USER, "Synthetic Teacher", "teacher", "active", False,
                                 "synthetic-v1", "synthetic-v1", school_ids=("10",))
        self.revoked = False
        self.failure = False
        self.reads = 0

    def authenticate(self, bearer):
        if self.failure:
            raise BackendUnavailable("synthetic secret must never reach response")
        if bearer != "synthetic-only" or self.revoked:
            raise InvalidSession()
        return Identity(USER, SESSION)

    def load_access(self, identity):
        self.reads += 1
        return self.state


class V1Tests(unittest.TestCase):
    def setUp(self):
        self.backend = SyntheticBackend()
        self.app = Flask(__name__)
        install_api_v1(self.app, self.backend)
        self.client = self.app.test_client()
        self.headers = {"Authorization": "Bearer synthetic-only"}
        self.records = {"1": {"teacher": USER, "parent": USER,
                              "expert": USER, "status": "Validated"}}

        def scope(state, record_id):
            record = self.records.get(record_id)
            return bool(record and record.get(state.role) == state.user_id and
                        (state.role != "parent" or record["status"] == "Validated"))

        self.app.add_url_rule("/api/v1/test-record/<record_id>", "api_v1.test_record",
                             require_access(roles={"teacher", "parent", "expert"},
                                            record_scope=scope)(lambda record_id: jsonify(data={"id": record_id})))
        self.app.add_url_rule("/api/v1/test-grants/<school_id>", "api_v1.test_grants",
                             require_access(permission="accounts.manage", school_scope=lambda school_id: school_id)(
                                 lambda school_id: jsonify(data={})))
        self.app.add_url_rule("/api/v1/test-global", "api_v1.test_global",
                             require_access(permission="accounts.manage")(lambda: jsonify(data={})))

    def get(self, path="/me", **kwargs):
        return self.client.get("/api/v1" + path, headers=self.headers, **kwargs)

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status)
        body = response.get_json()
        self.assertEqual(body["error"]["code"], code)
        self.assertEqual(body["error"]["fields"], {})
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(str(UUID(body["request_id"])), response.headers["X-Request-ID"])
        return body

    def test_health_is_public_liveness_and_uses_generated_request_ids(self):
        self.backend.failure = True
        first = self.client.get("/api/v1/health", headers={"X-Request-ID": "untrusted"})
        second = self.client.get("/api/v1/health")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json["data"], {"status": "ok"})
        self.assertNotEqual(first.json["request_id"], second.json["request_id"])
        self.assertEqual(self.backend.reads, 0)

    def test_missing_malformed_expired_and_legacy_tokens_denied(self):
        for header in ("", "Bearer", "Basic synthetic-only", "Bearer a b", "Bearer expired", "Bearer legacy-admin-token"):
            with self.subTest(header=header):
                self.assert_error(self.client.get("/api/v1/me", headers={"Authorization": header}), 401, "AUTHENTICATION_REQUIRED")
        self.assert_error(self.client.get("/api/v1/me?token=synthetic-only"), 401, "AUTHENTICATION_REQUIRED")

    def test_default_backend_fails_closed_without_legacy_fallback(self):
        app = Flask("unconfigured")
        install_api_v1(app)
        self.assert_error(app.test_client().get("/api/v1/me", headers=self.headers), 503, "SERVICE_UNAVAILABLE")

    def test_service_errors_do_not_expose_exception_text(self):
        self.backend.failure = True
        response = self.get()
        self.assert_error(response, 503, "SERVICE_UNAVAILABLE")
        self.assertNotIn("synthetic secret", response.get_data(as_text=True))

    def test_me_projection_has_no_session_or_private_adapter_data(self):
        body = self.get().json
        self.assertEqual(set(body), {"data", "request_id"})
        self.assertEqual(set(body["data"]), {"user_id", "full_name", "role", "account_status", "permissions", "school_ids", "onboarding"})
        self.assertEqual(body["data"]["onboarding"]["next_action"], "ready")
        self.assertEqual(body["data"]["school_ids"], ["10"])
        self.assertNotIn(SESSION, str(body))

    def test_bootstrap_exposes_gates_in_priority_order(self):
        for change, required, accepted, action in (
            (True, None, None, "change_password"),
            (False, None, None, "agreement_unavailable"),
            (False, "new-version", "old-version", "accept_privacy"),
            (False, "v1", "v1", "ready"),
        ):
            with self.subTest(action=action):
                self.backend.state = replace(self.backend.state, must_change_password=change,
                                             required_agreement_version=required, accepted_agreement_version=accepted)
                self.assertEqual(self.get().json["data"]["onboarding"]["next_action"], action)

    def test_unavailable_missing_or_mismatched_profiles_are_denied(self):
        original = self.backend.state
        for state in (None, replace(original, user_id=SESSION), replace(original, role="invented"),
                      *(replace(original, account_status=s) for s in ("pending", "disabled", "rejected"))):
            self.backend.state = state
            self.assert_error(self.get(), 403, "ACCOUNT_UNAVAILABLE")

    def test_revocation_and_current_profile_changes_apply_next_request(self):
        self.assertEqual(self.get().status_code, 200)
        self.backend.state = replace(self.backend.state, account_status="disabled")
        self.assert_error(self.get(), 403, "ACCOUNT_UNAVAILABLE")
        self.backend.revoked = True
        self.assert_error(self.get(), 401, "AUTHENTICATION_REQUIRED")
        self.assertEqual(self.backend.reads, 2)

    def test_resource_gates_run_before_record_or_permission_access(self):
        original = self.backend.state
        for change, required, accepted, status, code in (
            (True, None, None, 403, "PASSWORD_CHANGE_REQUIRED"),
            (False, None, None, 503, "AGREEMENT_NOT_CONFIGURED"),
            (False, "new", "old", 403, "PRIVACY_ACCEPTANCE_REQUIRED"),
        ):
            self.backend.state = replace(original, must_change_password=change,
                                         required_agreement_version=required, accepted_agreement_version=accepted)
            self.assert_error(self.get("/test-record/missing"), status, code)
            self.assert_error(self.get("/test-global"), status, code)

    def test_current_assignments_and_parent_review_release(self):
        for role in ("teacher", "parent", "expert"):
            self.backend.state = replace(self.backend.state, role=role)
            self.records["1"][role] = USER
            self.records["1"]["status"] = "Validated"
            self.assertEqual(self.get("/test-record/1").status_code, 200)
            self.records["1"][role] = SESSION
            inaccessible = self.get("/test-record/1")
            missing = self.get("/test-record/999")
            self.assert_error(inaccessible, 404, "NOT_FOUND")
            self.assertEqual(inaccessible.json["error"], missing.json["error"])
        self.backend.state = replace(self.backend.state, role="parent")
        self.records["1"]["parent"] = USER
        for status in ("Pending", "Flagged"):
            self.records["1"]["status"] = status
            self.assert_error(self.get("/test-record/1"), 404, "NOT_FOUND")

    def test_membership_and_client_role_cannot_authorize_records(self):
        self.records["1"]["teacher"] = SESSION
        self.assert_error(self.get("/test-record/1?role=admin&user_id=" + SESSION), 404, "NOT_FOUND")
        self.backend.state = replace(self.backend.state, role="guest")
        self.assert_error(self.get("/test-record/1"), 403, "FORBIDDEN")

    def test_explicit_grants_role_ceiling_and_school_scope(self):
        self.assert_error(self.get("/test-grants/10"), 403, "FORBIDDEN")
        self.backend.state = replace(self.backend.state, grants=(Grant("accounts.manage", "10"),))
        self.assert_error(self.get("/test-grants/10"), 403, "FORBIDDEN")
        self.assertEqual(self.get().json["data"]["permissions"], [])
        for role in ("admin", "researcher"):
            self.backend.state = replace(self.backend.state, role=role)
            self.assertEqual(self.get("/test-grants/10").status_code, 200)
            self.assert_error(self.get("/test-grants/11"), 403, "FORBIDDEN")
            self.assert_error(self.get("/test-global"), 403, "FORBIDDEN")
        self.backend.state = replace(self.backend.state, grants=(Grant("accounts.manage"),))
        self.assertEqual(self.get("/test-global").status_code, 200)
        self.assertEqual(self.get("/test-grants/11").status_code, 200)
        self.backend.state = replace(self.backend.state, grants=())
        self.assert_error(self.get("/test-global"), 403, "FORBIDDEN")

    def test_invalid_adapter_identity_and_unexpected_errors_are_sanitized(self):
        self.backend.authenticate = lambda bearer: Identity("invalid UUID with secret", SESSION)
        response = self.get()
        self.assert_error(response, 500, "INTERNAL_ERROR")
        self.assertNotIn("secret", response.get_data(as_text=True))

    def test_invalid_guard_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            require_access(permission="invented.power")
        with self.assertRaises(ValueError):
            require_access(bootstrap=True, roles={"admin"})


if __name__ == "__main__":
    unittest.main()
