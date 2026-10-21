"""The hosted checker is tested offline with fictional driver/HTTP fixtures."""

import json
import unittest
from unittest.mock import MagicMock, Mock

from tools.check_v1_hosted import (CONNECTION_SQL, SESSION_FUNCTION_SQL, TABLE_ACCESS_SQL, TABLES, TRIGGER_SQL,
                                   run_preflight)
from api_v1 import Identity, UnavailableBackend
from v1_backend import SNAPSHOT_SQL, SupabasePostgresBackend


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.env = {"GRAPHISCAN_V1_BACKEND": "supabase-postgres",
                    "GRAPHISCAN_V1_SUPABASE_URL": "https://synthetic.example.invalid",
                    "GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_synthetic_private",
                    "GRAPHISCAN_V1_DATABASE_URL": "synthetic_database_password",
                    "GRAPHISCAN_V1_TEST_ACCESS_TOKEN": "synthetic_bearer_private"}
        self.connection = MagicMock()
        self.cursor = self.connection.__enter__.return_value.cursor.return_value.__enter__.return_value
        self.info = dict(read_only=True, utc=True, bounded=True, restricted=True)
        self.access = dict(rls=True, schema_usage=True, can_select=True, can_write=False, owns_table=False)
        self.trigger = {"installed": True}
        self.session_function = {"installed": True, "auth_table_restricted": True}
        self.snapshot = {"session_valid": False, "user_id": None}
        self.executed = []

        def execute(sql, params=None):
            self.executed.append((sql, params))
            if sql == CONNECTION_SQL:
                self.cursor.fetchone.return_value = self.info
            elif sql == TABLE_ACCESS_SQL:
                self.cursor.fetchone.return_value = self.access
            elif sql == TRIGGER_SQL:
                self.cursor.fetchone.return_value = self.trigger
            elif sql == SESSION_FUNCTION_SQL:
                self.cursor.fetchone.return_value = self.session_function
            elif sql == SNAPSHOT_SQL:
                self.cursor.fetchone.return_value = self.snapshot
            else:
                raise AssertionError("Unexpected query")

        self.cursor.execute.side_effect = execute
        self.repo = Mock()
        self.repo.connect.return_value = self.connection
        self.repo.load_access.return_value = None
        self.verifier = Mock()
        self.verifier.authenticate.return_value = Identity("00000000-0000-4000-8000-000000000001", "00000000-0000-4000-8000-000000000002")
        self.backend = SupabasePostgresBackend(self.verifier, self.repo)
        self.factory = Mock(return_value=self.backend)

    def run_check(self, connect=True):
        return run_preflight(self.env, connect=connect, backend_factory=self.factory)

    def test_missing_configuration_is_reported_without_factory_or_network(self):
        result = run_preflight({}, connect=True, backend_factory=self.factory)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["network_attempted"])
        self.factory.assert_not_called()
        self.assertEqual(len(result["checks"]), 4)

    def test_offline_mode_never_connects_or_uses_supplied_bearer(self):
        result = self.run_check(connect=False)
        self.assertEqual(result["status"], "ready-to-connect")
        self.assertFalse(result["network_attempted"])
        self.repo.connect.assert_not_called()
        self.verifier.authenticate.assert_not_called()
        self.assertNotIn("synthetic_", json.dumps(result))

    def test_invalid_configuration_does_not_attempt_network(self):
        self.factory.return_value = UnavailableBackend()
        result = self.run_check()
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["network_attempted"])

    def test_read_only_schema_checks_use_parameters_and_no_real_identity(self):
        del self.env["GRAPHISCAN_V1_TEST_ACCESS_TOKEN"]
        result = self.run_check()
        self.assertEqual(result["status"], "preflight-passed")
        self.assertFalse(result["database_writes"])
        self.assertEqual([params[0] for sql, params in self.executed if sql == TABLE_ACCESS_SQL], list(TABLES))
        identity = self.executed[-1][1]
        self.assertEqual(set(identity.values()), {"00000000-0000-0000-0000-000000000000"})
        self.assertEqual(result["checks"][-1]["status"], "not-run")
        self.assertTrue(all(sql.lstrip().startswith(("SELECT", "--")) for sql, params in self.executed))
        self.connection.__exit__.assert_called_once()

    def test_wrong_connection_settings_and_privileged_role_stop_checks(self):
        for field in self.info:
            with self.subTest(field=field):
                self.info[field] = False
                result = self.run_check()
                self.assertEqual(result["status"], "failed")
                self.info[field] = True
        self.verifier.authenticate.assert_not_called()

    def test_bad_grants_ownership_or_disabled_rls_fail(self):
        for field, bad in (("schema_usage", False), ("can_select", False), ("can_write", True), ("owns_table", True), ("rls", False)):
            original = self.access[field]
            with self.subTest(field=field):
                self.access[field] = bad
                self.assertEqual(self.run_check()["status"], "failed")
                self.access[field] = original

    def test_missing_trigger_or_accidentally_allowed_zero_identity_fail(self):
        self.trigger["installed"] = False
        self.assertEqual(self.run_check()["status"], "failed")
        self.trigger["installed"] = True
        self.snapshot["session_valid"] = True
        self.assertEqual(self.run_check()["status"], "failed")

    def test_unrestricted_auth_table_or_missing_session_function_fail(self):
        for field in self.session_function:
            self.session_function[field] = False
            self.assertEqual(self.run_check()["status"], "failed")
            self.session_function[field] = True

    def test_errors_never_disclose_credentials_or_tracebacks(self):
        self.repo.connect.side_effect = RuntimeError("synthetic_database_password synthetic_bearer_private")
        result = self.run_check()
        text = json.dumps(result)
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("synthetic_", text)
        self.assertNotIn("Traceback", text)

    def test_bootstrap_denial_fails_without_disclosing_response(self):
        result = self.run_check()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["checks"][-1], {"name": "test_session_bootstrap", "status": "fail"})
        self.assertNotIn("synthetic_", json.dumps(result))

    def test_successful_bootstrap_omits_profile_and_session_values(self):
        from api_v1 import AccessState
        self.repo.load_access.return_value = AccessState(
            "00000000-0000-4000-8000-000000000001", "Synthetic Private Name", "teacher", "active", True)
        result = self.run_check()
        self.assertEqual(result["status"], "preflight-passed")
        text = json.dumps(result)
        for secret in ("Synthetic Private Name", "00000000-0000-4000-8000-000000000001", "synthetic_bearer_private"):
            self.assertNotIn(secret, text)


if __name__ == "__main__":
    unittest.main()
