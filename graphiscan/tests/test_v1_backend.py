"""Adapter tests use synthetic HTTP responses and DB connections only."""

import base64
import json
import importlib.util
import unittest
from unittest.mock import Mock, patch

import requests
from flask import Flask

from api_v1 import BackendUnavailable, Identity, InvalidSession, UnavailableBackend, install_api_v1
from v1_backend import (PostgresAccessRepository, SNAPSHOT_SQL, SupabaseIdentityVerifier,
                        SupabasePostgresBackend, backend_from_environment)


USER = "00000000-0000-4000-8000-000000000001"
SESSION = "00000000-0000-4000-8000-000000000002"
ORIGIN = "https://synthetic-project.example.invalid"
KEY = "sb_publishable_synthetic_only"


def token(**overrides):
    claims = dict(sub=USER, session_id=SESSION, aud="authenticated", iss=ORIGIN + "/auth/v1", iat=900, exp=1100)
    claims.update(overrides)
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    # Deliberately not a signed JWT: the mocked provider alone accepts it.
    return "synthetic-header." + payload + ".synthetic-signature"


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.response = Mock(status_code=200)
        self.response.json.return_value = {"id": USER, "user_metadata": {"role": "admin"}}
        self.get = Mock(return_value=self.response)
        self.verifier = SupabaseIdentityVerifier(ORIGIN, KEY, get=self.get, now=lambda: 1000)

    def test_exact_token_verified_remotely_before_claims_used(self):
        bearer = token()
        self.assertEqual(self.verifier.authenticate(bearer), Identity(USER, SESSION))
        self.get.assert_called_once_with(ORIGIN + "/auth/v1/user", headers={"apikey": KEY, "Authorization": "Bearer " + bearer}, timeout=(3.05, 5), allow_redirects=False)
        self.response.close.assert_called_once()

    def test_provider_denial_never_uses_locally_plausible_claims(self):
        for status in (401, 403):
            self.response.status_code = status
            with self.assertRaises(InvalidSession):
                self.verifier.authenticate(token())
        self.response.json.assert_not_called()

    def test_outage_rate_limit_and_redirect_fail_closed(self):
        for status in (301, 302, 400, 429, 500, 503):
            self.response.status_code = status
            with self.assertRaises(BackendUnavailable):
                self.verifier.authenticate(token())
        self.get.side_effect = requests.Timeout("synthetic private endpoint")
        with self.assertRaises(BackendUnavailable):
            self.verifier.authenticate(token())

    def test_claim_boundaries_and_provider_subject_binding(self):
        cases = [dict(sub=SESSION), dict(sub="invalid"), dict(session_id=None), dict(iss="https://untrusted.invalid/auth/v1"),
                 dict(aud="service_role"), dict(exp=1000), dict(exp=800), dict(iat=1001), dict(iat=True),
                 dict(exp=float("inf")), dict(nbf=1001), dict(nbf="900")]
        for claims in cases:
            with self.subTest(claims=claims), self.assertRaises(InvalidSession):
                self.verifier.authenticate(token(**claims))
        self.assertEqual(self.verifier.authenticate(token(aud=["authenticated"], nbf=999)), Identity(USER, SESSION))

    def test_malformed_tokens_and_missing_claims(self):
        for bearer in ("legacy-token", "a.b", "a.b.c.d", "a." + "b" * 17000 + ".c"):
            with self.assertRaises(InvalidSession):
                self.verifier.authenticate(bearer)
        self.get.assert_not_called()
        for payload in ("%%%", "e30", "bnVsbA", "W10"):
            with self.assertRaises(InvalidSession):
                self.verifier.authenticate("a." + payload + ".c")

    def test_malformed_provider_response_is_service_failure(self):
        for value in (None, [], {}, {"id": None}):
            self.response.json.return_value = value
            with self.assertRaises(BackendUnavailable):
                self.verifier.authenticate(token())
        self.response.json.side_effect = ValueError("synthetic secret")
        with self.assertRaises(BackendUnavailable):
            self.verifier.authenticate(token())

    def test_only_trusted_https_origin_and_publishable_key_accepted(self):
        for origin in ("http://localhost", "https://user:pass@example.invalid", ORIGIN + "/auth/v1", ORIGIN + "?key=x", ORIGIN + "#x"):
            with self.assertRaises(ValueError):
                SupabaseIdentityVerifier(origin, KEY)
        with self.assertRaises(ValueError):
            SupabaseIdentityVerifier(ORIGIN, "sb_secret_synthetic")


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(session_valid=True, user_id=USER, full_name="Synthetic Teacher", role="teacher",
                        account_status="active", must_change_password=False,
                        required_agreement_version="synthetic-v1", accepted_agreement_version="synthetic-v1",
                        grants=[{"permission": "accounts.manage", "school_id": "10"}], school_ids=["10"])
        self.connect = Mock()
        # Context manager protocols need MagicMock, not a bare Mock.
        from unittest.mock import MagicMock
        self.connection = MagicMock()
        self.connect.return_value = self.connection
        self.cursor = self.connection.__enter__.return_value.cursor.return_value.__enter__.return_value
        self.cursor.fetchone.side_effect = lambda: self.row
        self.repo = PostgresAccessRepository(self.connect)
        self.identity = Identity(USER, SESSION)

    def test_parameterized_single_snapshot_and_projection(self):
        state = self.repo.load_access(self.identity)
        self.cursor.execute.assert_called_once_with(SNAPSHOT_SQL, {"user_id": USER, "session_id": SESSION})
        self.assertEqual(state.user_id, USER)
        self.assertEqual(state.grants[0].school_id, "10")
        self.assertEqual(state.school_ids, ("10",))
        self.connection.__exit__.assert_called_once()

    def test_durable_session_denial_precedes_profile_projection(self):
        self.row["session_valid"] = False
        self.row["user_id"] = None
        with self.assertRaises(InvalidSession):
            self.repo.load_access(self.identity)

    def test_missing_profile_is_not_created_or_fabricated(self):
        self.row["user_id"] = None
        self.assertIsNone(self.repo.load_access(self.identity))

    def test_driver_and_snapshot_errors_are_sanitized(self):
        self.connect.side_effect = RuntimeError("synthetic database password")
        with self.assertRaises(BackendUnavailable) as error:
            self.repo.load_access(self.identity)
        self.assertNotIn("password", str(error.exception))
        self.connect.side_effect = None
        self.row = None
        with self.assertRaises(BackendUnavailable):
            self.repo.load_access(self.identity)

    def test_full_bootstrap_chain_refreshes_profile_and_session_each_request(self):
        response = Mock(status_code=200)
        response.json.return_value = {"id": USER}
        get = Mock(return_value=response)
        backend = SupabasePostgresBackend(SupabaseIdentityVerifier(ORIGIN, KEY, get=get, now=lambda: 1000), self.repo)
        app = Flask(__name__)
        install_api_v1(app, backend)
        client = app.test_client()
        headers = {"Authorization": "Bearer " + token(role="admin")}
        first = client.get("/api/v1/me", headers=headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json["data"]["role"], "teacher")
        self.row["account_status"] = "disabled"
        self.assertEqual(client.get("/api/v1/me", headers=headers).status_code, 403)
        self.row["session_valid"] = False
        self.assertEqual(client.get("/api/v1/me", headers=headers).status_code, 401)
        self.assertEqual(get.call_count, 3)
        self.assertEqual(self.cursor.execute.call_count, 3)


class ConfigurationTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("psycopg"), "Optional requirements-v1.txt not installed")
    def test_real_driver_parses_configuration_and_tls_overrides_dsn(self):
        import psycopg
        config = {"GRAPHISCAN_V1_BACKEND": "supabase-postgres", "GRAPHISCAN_V1_SUPABASE_URL": ORIGIN,
                  "GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY": KEY,
                  "GRAPHISCAN_V1_DATABASE_URL": "postgresql://fixture:synthetic@db.example.invalid/test?sslmode=disable"}
        with patch.object(psycopg, "connect") as connect:
            backend = backend_from_environment(config)
            self.assertIsInstance(backend, SupabasePostgresBackend)
            connect.assert_not_called()
            backend.repository.connect()
            self.assertEqual(connect.call_args.kwargs["sslmode"], "verify-full")
            config["GRAPHISCAN_V1_DATABASE_URL"] = "invalid conninfo"
            self.assertIsInstance(backend_from_environment(config), UnavailableBackend)

    def test_disabled_or_partial_configuration_is_unavailable(self):
        for config in ({}, {"GRAPHISCAN_V1_BACKEND": "unknown"}, {"GRAPHISCAN_V1_BACKEND": "supabase-postgres"}):
            self.assertIsInstance(backend_from_environment(config), UnavailableBackend)

    def test_opt_in_wires_verified_read_only_connection_without_connecting(self):
        import sys
        from types import ModuleType
        psycopg = ModuleType("psycopg")
        psycopg.connect = Mock()
        psycopg.conninfo = Mock()
        rows = ModuleType("psycopg.rows")
        rows.dict_row = object()
        config = {"GRAPHISCAN_V1_BACKEND": "supabase-postgres", "GRAPHISCAN_V1_SUPABASE_URL": ORIGIN,
                  "GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY": KEY, "GRAPHISCAN_V1_DATABASE_URL": "synthetic-dsn"}
        with patch.dict(sys.modules, {"psycopg": psycopg, "psycopg.rows": rows}):
            backend = backend_from_environment(config)
            self.assertIsInstance(backend, SupabasePostgresBackend)
            psycopg.connect.assert_not_called()
            backend.repository.connect()
        arguments = psycopg.connect.call_args.kwargs
        self.assertEqual(arguments["sslmode"], "verify-full")
        self.assertEqual(arguments["connect_timeout"], 5)
        self.assertIn("default_transaction_read_only=on", arguments["options"])
        self.assertIn("statement_timeout=5000", arguments["options"])

    @unittest.skipUnless(importlib.util.find_spec("psycopg"), "Optional requirements-v1.txt not installed")
    def test_password_writer_is_separate_tls_verified_and_function_only_composition(self):
        import psycopg
        config = {"GRAPHISCAN_V1_BACKEND": "supabase-postgres", "GRAPHISCAN_V1_SUPABASE_URL": ORIGIN,
                  "GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY": KEY,
                  "GRAPHISCAN_V1_DATABASE_URL": "postgresql://graphiscan_api_reader:synthetic@db.example.invalid/test",
                  "GRAPHISCAN_V1_PASSWORD_DATABASE_URL": "postgresql://graphiscan_password_writer.fixture:synthetic@db.example.invalid/test?sslmode=disable"}
        with patch.object(psycopg, "connect") as connect:
            backend = backend_from_environment(config)
            self.assertIsNotNone(backend.password_service)
            connect.assert_not_called()
            backend.password_service.repository.connect()
            self.assertEqual(connect.call_args.kwargs['sslmode'], 'verify-full')
            self.assertIn('lock_timeout=3000', connect.call_args.kwargs['options'])
            self.assertNotIn('read_only=on', connect.call_args.kwargs['options'])
            self.assertEqual([call.args[0] for call in connect.return_value.execute.call_args_list], [
                "SET SESSION TIME ZONE 'UTC'", "SET SESSION statement_timeout = '5s'",
                "SET SESSION lock_timeout = '3s'"])
            connect.return_value.commit.assert_called_once()
            backend.repository.connect()
            self.assertIn('read_only=on', connect.call_args.kwargs['options'])
        for role in ('postgres', 'graphiscan_api_reader'):
            config['GRAPHISCAN_V1_PASSWORD_DATABASE_URL'] = f'postgresql://{role}:synthetic@db.example.invalid/test'
            self.assertIsInstance(backend_from_environment(config), UnavailableBackend)


if __name__ == "__main__":
    unittest.main()
