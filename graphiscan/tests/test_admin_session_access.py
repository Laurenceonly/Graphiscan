"""Admin sessions must follow current account state, not stale token claims."""

import unittest
from unittest.mock import Mock, patch

from flask import g, jsonify

from app import ADMIN_TOKENS, app, require_admin_api


class AdminSessionAccessTests(unittest.TestCase):
    def setUp(self):
        self.token = "synthetic-admin-session"
        ADMIN_TOKENS[self.token] = {"user_id": 91, "role": "admin"}
        self.account = {
            "user_id": 91, "fullname": "Synthetic Admin",
            "email": "admin@example.invalid", "role": "admin", "account_status": "active",
        }
        self.connection = Mock()
        self.cursor = self.connection.cursor.return_value
        self.cursor.fetchone.return_value = self.account
        self.connection_patch = patch("app.get_db_connection", return_value=self.connection)
        self.connection_patch.start()
        self.action = Mock(side_effect=lambda: jsonify({"role": g.current_admin["role"]}))
        self.protected = require_admin_api(self.action)

    def tearDown(self):
        self.connection_patch.stop()
        ADMIN_TOKENS.pop(self.token, None)

    def request(self, token=None):
        headers = {} if token is None else {"Authorization": "Bearer " + token}
        with app.test_request_context(headers=headers):
            return app.make_response(self.protected())

    def test_active_admin_can_access_and_session_is_refreshed(self):
        response = self.request(self.token)
        self.assertEqual(response.status_code, 200)
        self.action.assert_called_once()
        self.assertEqual(ADMIN_TOKENS[self.token]["email"], self.account["email"])
        self.cursor.close.assert_called_once()
        self.connection.close.assert_called_once()

    def test_inactive_admin_is_denied_and_session_revoked(self):
        for status in ("disabled", "pending", "rejected"):
            with self.subTest(status=status):
                ADMIN_TOKENS[self.token] = {"user_id": 91, "role": "admin"}
                self.account["account_status"] = status
                self.assertEqual(self.request(self.token).status_code, 403)
                self.assertNotIn(self.token, ADMIN_TOKENS)
        self.action.assert_not_called()

    def test_deleted_admin_is_denied_and_session_revoked(self):
        self.cursor.fetchone.return_value = None
        self.assertEqual(self.request(self.token).status_code, 401)
        self.assertNotIn(self.token, ADMIN_TOKENS)
        self.action.assert_not_called()

    def test_changed_role_cannot_use_old_admin_session(self):
        self.account["role"] = "teacher"
        self.assertEqual(self.request(self.token).status_code, 403)
        self.assertNotIn(self.token, ADMIN_TOKENS)
        self.action.assert_not_called()

    def test_missing_or_unknown_token_is_denied_before_database_access(self):
        for token in (None, "unknown-session"):
            with self.subTest(token=token):
                self.assertEqual(self.request(token).status_code, 401)
        self.connection.cursor.assert_not_called()
        self.action.assert_not_called()


if __name__ == "__main__":
    unittest.main()
