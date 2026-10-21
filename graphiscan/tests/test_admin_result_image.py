"""Admin image access must not depend on an expert review date."""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from app import app, api_admin_result_detail
from api_v1 import UnavailableBackend


class AdminResultImageTests(unittest.TestCase):
    def test_v1_foundation_registered_without_legacy_session_fallback(self):
        client = app.test_client()
        health = client.get("/api/v1/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json["data"], {"status": "ok"})
        self.assertEqual(client.get("/api/v1/me").status_code, 401)
        # Local v1 setup may be enabled; isolate this unavailable-backend case
        # so synthetic regression tests never contact configured services.
        with patch.dict(app.extensions, {"graphiscan_v1_backend": UnavailableBackend()}):
            denied = client.get("/api/v1/me", headers={"Authorization": "Bearer synthetic-unconfigured"})
        self.assertEqual(denied.status_code, 503)
        self.assertEqual(denied.json["error"]["code"], "SERVICE_UNAVAILABLE")
        self.assertEqual(denied.headers["Cache-Control"], "no-store")
        self.assertFalse(any("test-record" in str(rule) for rule in app.url_map.iter_rules()))

    def test_image_url_present_before_and_after_review(self):
        for review_date in (None, datetime(2026, 10, 19, 12, 0)):
            with self.subTest(reviewed=review_date is not None):
                cursor = Mock()
                cursor.fetchone.return_value = {
                    "date_generated": datetime(2026, 10, 18, 12, 0),
                    "validation_date": review_date,
                    "image_path": "static/uploads/synthetic.png",
                }
                connection = Mock()
                connection.cursor.return_value = cursor
                with patch("app.get_db_connection", return_value=connection):
                    with app.test_request_context(base_url="http://localhost/"):
                        # Exercise the route body; guard behavior has its own suite.
                        response = api_admin_result_detail.__wrapped__(123)
                result = response.get_json()["result"]
                self.assertEqual(result["image_url"], "http://localhost/static/uploads/synthetic.png")
                self.assertEqual(result["validation_date"], str(review_date) if review_date else None)
                cursor.close.assert_called_once()
                connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
