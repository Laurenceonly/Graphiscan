"""Synthetic-record checks for parent result release and ownership."""

import sqlite3
import unittest
from unittest.mock import patch

from app import USER_TOKENS, app


class DictionaryCursor:
    def __init__(self, connection):
        self.cursor = connection.cursor()

    def execute(self, query, parameters=()):
        self.cursor.execute(query.replace("%s", "?"), parameters)

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self):
        return [dict(row) for row in self.cursor.fetchall()]

    def close(self):
        self.cursor.close()


class TestConnection:
    def __init__(self):
        self.database = sqlite3.connect(":memory:")
        self.database.row_factory = sqlite3.Row

    def cursor(self, dictionary=False):
        return DictionaryCursor(self.database)

    def close(self):
        pass


class ParentResultAccessTests(unittest.TestCase):
    def setUp(self):
        self.connection = TestConnection()
        self.connection.database.executescript("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY, fullname TEXT, email TEXT,
                role TEXT, account_status TEXT
            );
            CREATE TABLE students (
                student_id INTEGER PRIMARY KEY, fullname TEXT, age INTEGER,
                grade_level TEXT, teacher_id INTEGER, parent_id INTEGER
            );
            CREATE TABLE handwriting_samples (
                sample_id INTEGER PRIMARY KEY, student_id INTEGER,
                teacher_id INTEGER, image_path TEXT
            );
            CREATE TABLE results (
                result_id INTEGER PRIMARY KEY, sample_id INTEGER,
                classification TEXT, dysgraphia_probability REAL,
                confidence_score REAL, analysis_summary TEXT,
                date_generated TEXT
            );
            CREATE TABLE validations (
                result_id INTEGER, validation_status TEXT, remarks TEXT,
                expert_recommendation TEXT, follow_up_needed TEXT,
                validation_date TEXT, expert_id INTEGER
            );
            INSERT INTO users VALUES (1, 'Parent One', 'one@example.invalid', 'parent', 'active');
            INSERT INTO users VALUES (2, 'Parent Two', 'two@example.invalid', 'parent', 'active');
            INSERT INTO users VALUES (3, 'Teacher', 'teacher@example.invalid', 'teacher', 'active');
            INSERT INTO students VALUES (10, 'Child One', 8, '2', 3, 1);
            INSERT INTO students VALUES (20, 'Child Two', 8, '2', 3, 2);
            INSERT INTO handwriting_samples VALUES (100, 10, 3, 'sample.png');
            INSERT INTO handwriting_samples VALUES (101, 10, 3, 'sample.png');
            INSERT INTO handwriting_samples VALUES (102, 10, 3, 'sample.png');
            INSERT INTO handwriting_samples VALUES (200, 20, 3, 'sample.png');
            INSERT INTO results VALUES (1000, 100, 'High Potential', 90, 90, '', '2026-10-01');
            INSERT INTO results VALUES (1001, 101, 'High Potential', 90, 90, '', '2026-10-02');
            INSERT INTO results VALUES (1002, 102, 'Normal', 10, 90, '', '2026-10-03');
            INSERT INTO results VALUES (2000, 200, 'Normal', 10, 90, '', '2026-10-04');
            INSERT INTO validations VALUES (1000, 'Pending', '', '', 'No', NULL, NULL);
            INSERT INTO validations VALUES (1001, 'Flagged', '', '', 'No', NULL, NULL);
            INSERT INTO validations VALUES (1002, 'Validated', 'Reviewed', '', 'No', '2026-10-03', NULL);
            INSERT INTO validations VALUES (2000, 'Validated', 'Reviewed', '', 'No', '2026-10-04', NULL);
        """)
        self.connection_patch = patch("app.get_db_connection", return_value=self.connection)
        self.connection_patch.start()
        USER_TOKENS["synthetic-parent-token"] = {"user_id": 1, "role": "parent"}
        self.client = app.test_client()
        self.headers = {"Authorization": "Bearer synthetic-parent-token"}

    def tearDown(self):
        USER_TOKENS.pop("synthetic-parent-token", None)
        self.connection_patch.stop()
        self.connection.database.close()

    def test_parent_api_returns_only_owned_validated_results(self):
        response = self.client.get("/api/user/parent/results", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["result_id"] for row in response.json["results"]], [1002])

        response = self.client.get("/api/user/parent/students/10/progress", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["result_id"] for row in response.json["progress"]], [1002])

        for result_id in (1000, 1001, 2000):
            response = self.client.get(f"/api/user/parent/results/{result_id}", headers=self.headers)
            self.assertEqual(response.status_code, 404)
            response = self.client.get(
                f"/api/user/results/{result_id}/download-image", headers=self.headers
            )
            self.assertEqual(response.status_code, 404)

        response = self.client.get("/api/user/parent/results/1002", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["result"]["validation_status"], "Validated")

        response = self.client.get("/api/user/parent/students/20/progress", headers=self.headers)
        self.assertEqual(response.status_code, 404)

        with patch("app.os.path.exists", return_value=True), patch(
            "app.send_file", return_value="image allowed"
        ):
            response = self.client.get(
                "/api/user/results/1002/download-image", headers=self.headers
            )
        self.assertEqual(response.status_code, 200)

    def test_legacy_parent_paths_withhold_unreviewed_results(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["role"] = "parent"

        response = self.client.get("/parent/results")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Child One", response.data)
        self.assertNotIn(b"High Potential", response.data)

        for result_id in (1000, 1001, 2000):
            for route in ("result", "report"):
                response = self.client.get(f"/{route}/{result_id}")
                self.assertEqual(response.status_code, 302)


if __name__ == "__main__":
    unittest.main()
