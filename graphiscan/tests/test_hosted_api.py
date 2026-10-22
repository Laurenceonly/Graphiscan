"""Hosted composition checks use fictional configuration and never connect."""
import unittest

from api_v1 import ApiError, UnavailableBackend
from hosted_api import create_app
from v1_backend import SupabasePostgresBackend, backend_from_environment


def configuration():
    return {
        "GRAPHISCAN_V1_BACKEND": "supabase-postgres",
        "GRAPHISCAN_V1_SUPABASE_URL": "https://fixture.example.invalid",
        "GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_fixture_only",
        "GRAPHISCAN_V1_DATABASE_URL": "postgresql://graphiscan_api_reader:fixture@db.example.invalid/test",
        "GRAPHISCAN_V1_PASSWORD_DATABASE_URL": "postgresql://graphiscan_password_writer:fixture@db.example.invalid/test",
        "GRAPHISCAN_V1_ADMIN_DATABASE_URL": "postgresql://graphiscan_admin_writer:fixture@db.example.invalid/test",
        "GRAPHISCAN_V1_CURSOR_SECRET": "ab" * 32,
        "GRAPHISCAN_CORS_ALLOWED_ORIGINS": "https://admin.example.invalid",
        "GRAPHISCAN_REQUIRE_MODEL": "false",
    }


class HostedCompositionTests(unittest.TestCase):
    def test_liveness_protected_routes_and_absent_legacy_routes(self):
        client = create_app(configuration()).test_client()
        response = client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        for path in ("/api/v1/accounts", "/api/v1/audit-logs", "/api/v1/students"):
            self.assertEqual(client.get(path).status_code, 401)
        for path in ("/api/admin/users", "/admin/dashboard", "/static/uploads/fixture.png"):
            self.assertEqual(client.get(path).status_code, 404)

    def test_cors_preflight_allows_only_configured_https_origin(self):
        client = create_app(configuration()).test_client()
        for origin, allowed in (("https://admin.example.invalid", True),
                                ("https://foreign.example.invalid", False)):
            response = client.options("/api/v1/screenings", headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type,idempotency-key",
            })
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin if allowed else None)
            if allowed:
                self.assertIn("idempotency-key", response.headers["Access-Control-Allow-Headers"].lower())

    def test_startup_rejects_missing_adapter_model_writer_and_invalid_origins(self):
        for key, value in (("GRAPHISCAN_V1_CURSOR_SECRET", "x" * 64),
                           ("GRAPHISCAN_V1_BACKEND", ""),
                           ("GRAPHISCAN_V1_PASSWORD_DATABASE_URL", ""),
                           ("GRAPHISCAN_REQUIRE_MODEL", "true"),
                           ("GRAPHISCAN_CORS_ALLOWED_ORIGINS", ""),
                           ("GRAPHISCAN_CORS_ALLOWED_ORIGINS", "http://admin.example.invalid"),
                           ("GRAPHISCAN_CORS_ALLOWED_ORIGINS", "https://*.example.invalid"),
                           ("GRAPHISCAN_CORS_ALLOWED_ORIGINS", "https://admin.example.invalid/path")):
            with self.subTest(key=key, value=value):
                config = configuration()
                config[key] = value
                with self.assertRaises(RuntimeError):
                    create_app(config)

    def test_cursors_survive_new_instances_but_reject_different_actor_or_key(self):
        first = backend_from_environment(configuration())
        second = backend_from_environment(configuration())
        self.assertIsInstance(first, SupabasePostgresBackend)
        self.assertIsInstance(second, SupabasePostgresBackend)
        binding = ["fixture-actor", "fixture-session", "students"]
        timestamp = "2026-10-22T00:00:00+00:00"
        for service in ("directory_service", "admin_read_service", "screening_read_service",
                        "screening_upload_service", "assignment_options_service"):
            token = getattr(first, service).encode_cursor(binding, timestamp, "1")
            self.assertEqual(getattr(second, service).decode_cursor(token, binding), (timestamp, "1"))
        with self.assertRaises(ApiError):
            second.directory_service.decode_cursor(token, ["foreign-actor"])
        config = configuration()
        config["GRAPHISCAN_V1_CURSOR_SECRET"] = "cd" * 32
        with self.assertRaises(ApiError):
            backend_from_environment(config).directory_service.decode_cursor(token, binding)
        config["GRAPHISCAN_V1_CURSOR_SECRET"] = "invalid"
        self.assertIsInstance(backend_from_environment(config), UnavailableBackend)


if __name__ == "__main__":
    unittest.main()
