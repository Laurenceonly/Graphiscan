"""Execute the actual read-route SQL against isolated fictional SQLite records.

Route bodies are extracted without importing config, model or live connections.
SQLite verifies read/projection/scope behavior; it is not a live MySQL check.
Authentication decorators are retained in production and checked separately.
"""
import ast
from pathlib import Path
import sqlite3
import unittest
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import Mock
import os
from types import SimpleNamespace

from flask import Flask, g, jsonify, request
from werkzeug.utils import secure_filename

ROUTES = [f"api_{role}_{suffix}" for role in ("teacher", "expert", "parent")
          for suffix in ("results", "result_detail", "student_progress")]
SOURCE = ast.parse((Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8"))


class Cursor:
    def __init__(self, connection):
        self.cursor = connection.cursor()
    def execute(self, sql, params=()):
        self.cursor.execute(sql.replace("%s", "?"), params)
    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row else None
    def fetchall(self):
        return [dict(row) for row in self.cursor.fetchall()]
    def close(self):
        self.cursor.close()


class Connection:
    def __init__(self, connection):
        self.connection = connection
    def cursor(self, dictionary=True):
        return Cursor(self.connection)
    def close(self):
        pass


class ScreeningTypeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE users(user_id INTEGER, fullname TEXT);
            CREATE TABLE students(student_id INTEGER, fullname TEXT, age INTEGER,
                                  grade_level TEXT, teacher_id INTEGER, parent_id INTEGER);
            CREATE TABLE handwriting_samples(sample_id INTEGER, student_id INTEGER,
                                             teacher_id INTEGER, image_path TEXT);
            CREATE TABLE results(result_id INTEGER, sample_id INTEGER, classification TEXT,
                                 confidence_score REAL, dysgraphia_probability REAL,
                                 analysis_summary TEXT, date_generated TEXT);
            CREATE TABLE validations(result_id INTEGER, validation_status TEXT, remarks TEXT,
                                     expert_recommendation TEXT, follow_up_needed TEXT,
                                     expert_id INTEGER, validation_date TEXT);
            CREATE TABLE reports(report_id INTEGER, result_id INTEGER, student_id INTEGER, report_type TEXT);
            INSERT INTO users VALUES(11,'Fictional teacher'),(12,'Other teacher'),
                                    (21,'Fictional parent'),(22,'Other parent'),(51,'Fictional expert');
            INSERT INTO students VALUES(1,'Fictional child',7,'Grade 1',11,21),
                                       (2,'Other child',8,'Grade 2',12,22);
            INSERT INTO handwriting_samples VALUES(31,1,11,'synthetic.png'),(32,2,12,'synthetic.png');
            INSERT INTO results VALUES
              (41,31,'High Potential',80,80,'','2026-10-01'),
              (42,31,'Normal',80,20,'','2026-10-02'),
              (43,32,'Normal',90,10,'','2026-10-03'),
              (44,31,'Normal',90,10,'','2026-10-04'),
              (45,31,'Normal',90,10,'','2026-10-05');
            INSERT INTO validations VALUES
              (41,'Pending','','','No',NULL,NULL),
              (42,'Validated','Review','Expert note','No',51,'2026-10-02'),
              (43,'Validated','Review','Expert note','No',51,'2026-10-03'),
              (44,'Validated','Review','Expert note','No',51,'2026-10-04'),
              (45,'Validated','Review','Expert note','No',51,'2026-10-05');
            INSERT INTO reports VALUES(1,41,1,'Initial Screening'),(2,42,1,'Follow-up Screening'),
              (3,43,2,'Initial Screening'),(4,45,1,'Initial Screening'),(5,45,1,'Follow-up Screening');
        """)
        namespace = {"get_db_connection": lambda: Connection(self.db), "g": g,
                     "jsonify": jsonify, "build_image_url": lambda path: None}
        for node in SOURCE.body:
            if isinstance(node, ast.FunctionDef) and node.name in ROUTES:
                # Copy before removing decorators so source guard evidence stays intact.
                body = ast.parse(ast.unparse(node)).body[0]
                body.decorator_list = []
                exec(compile(ast.Module(body=[body], type_ignores=[]), "app-read-routes", "exec"), namespace)
        self.routes = namespace
        self.app = Flask(__name__)

    def tearDown(self):
        self.db.close()

    def call(self, role, suffix, *args, user_id=None):
        with self.app.test_request_context():
            g.current_user = {"user_id": user_id or {"teacher": 11, "parent": 21, "expert": 51}[role]}
            response = self.app.make_response(self.routes[f"api_{role}_{suffix}"](*args))
            return response.status_code, response.get_json()

    def test_all_nine_reads_keep_role_guards_and_return_recorded_types(self):
        for node in SOURCE.body:
            if isinstance(node, ast.FunctionDef) and node.name in ROUTES:
                role = node.name.split("_")[1]
                self.assertIn(f"require_user_api(['{role}'])", [ast.unparse(d) for d in node.decorator_list])
        for role in ("teacher", "expert", "parent"):
            for suffix, args, key in (("results", (), "results"),
                                      ("result_detail", (42,), "result"),
                                      ("student_progress", (1,), "progress")):
                with self.subTest(role=role, suffix=suffix):
                    status, body = self.call(role, suffix, *args)
                    self.assertEqual(status, 200)
                    rows = body[key] if isinstance(body[key], list) else [body[key]]
                    row = next(row for row in rows if row["result_id"] == 42)
                    self.assertEqual(row["report_type"], "Follow-up Screening")
                    self.assertEqual(row["confidence_score"], 80)

    def test_parent_first_visible_record_keeps_follow_up_type_and_release_filter(self):
        _, body = self.call("parent", "student_progress", 1)
        self.assertEqual(body["progress"][0]["result_id"], 42)
        self.assertEqual(body["progress"][0]["report_type"], "Follow-up Screening")
        _, body = self.call("parent", "results")
        self.assertEqual({r["result_id"] for r in body["results"]}, {42, 44, 45})
        self.assertEqual(self.call("parent", "result_detail", 41)[0], 404)
        self.assertEqual(self.call("parent", "result_detail", 43)[0], 404)
        self.assertEqual(self.call("parent", "student_progress", 2)[0], 404)

    def test_teacher_scope_and_navigation_student_id_are_preserved(self):
        _, body = self.call("teacher", "results")
        self.assertNotIn(43, [r["result_id"] for r in body["results"]])
        self.assertTrue(all(r["student_id"] == 1 for r in body["results"]))
        _, body = self.call("teacher", "result_detail", 42)
        self.assertEqual(body["result"]["student_id"], 1)
        self.assertEqual(self.call("teacher", "result_detail", 43)[0], 404)
        self.assertEqual(self.call("teacher", "student_progress", 2)[0], 404)

    def test_missing_conflicting_or_wrong_student_reports_do_not_invent_a_type(self):
        self.db.execute("INSERT INTO reports VALUES(6,44,2,'Initial Screening')")
        _, body = self.call("expert", "results")
        rows = {row["result_id"]: row for row in body["results"]}
        self.assertEqual(len(rows), 5)
        self.assertIsNone(rows[44]["report_type"])
        self.assertIsNone(rows[45]["report_type"])

    def test_duplicate_matching_reports_do_not_duplicate_screening_rows(self):
        self.db.execute("INSERT INTO reports VALUES(6,42,1,'Follow-up Screening')")
        _, body = self.call("teacher", "results")
        rows = [row for row in body["results"] if row["result_id"] == 42]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["report_type"], "Follow-up Screening")

    def test_api_upload_saves_initial_and_follow_up_with_dictionary_cursor(self):
        source = next(node for node in SOURCE.body if isinstance(node, ast.FunctionDef) and node.name == "api_teacher_upload_sample")
        for count, expected in ((0, "Initial Screening"), (2, "Follow-up Screening")):
            with self.subTest(previous_reports=count), TemporaryDirectory() as folder:
                cursor, connection = Mock(), Mock()
                connection.cursor.return_value = cursor
                cursor.fetchone.side_effect = [{"student_id": 1}, {"report_count": count}]
                cursor.lastrowid = 77
                self.app.config["UPLOAD_FOLDER"] = folder
                namespace = {"app": self.app, "g": g, "jsonify": jsonify, "request": request,
                    "get_db_connection": lambda: connection, "allowed_file": lambda name: True,
                    "secure_filename": secure_filename, "os": os, "random": SimpleNamespace(randint=lambda a, b: 1000),
                    "run_handwriting_screening": lambda path: {"classification": "Normal", "confidence_score": 80,
                        "dysgraphia_probability": 20, "analysis_summary": ""}, "log_action": Mock()}
                body = ast.parse(ast.unparse(source)).body[0]
                body.decorator_list = []
                exec(compile(ast.Module(body=[body], type_ignores=[]), "app-upload-route", "exec"), namespace)
                with self.app.test_request_context(method="POST", data={"student_id": "1",
                    "handwriting_image": (BytesIO(b"fictional image; predictor stubbed"), "synthetic.png")}):
                    g.current_user = {"user_id": 11}
                    response = namespace["api_teacher_upload_sample"]()
                    self.assertTrue(response.get_json()["success"])
                report_insert = next(call for call in cursor.execute.call_args_list if "INSERT INTO reports" in call.args[0])
                self.assertEqual(report_insert.args[1][2], expected)
                connection.commit.assert_called_once()

    def test_legacy_upload_count_uses_dictionary_cursor_row(self):
        node = next(node for node in SOURCE.body if isinstance(node, ast.FunctionDef) and node.name == "upload_sample")
        calls = [n for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "execute" and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str) and "AS report_count" in n.args[0].value]
        self.assertEqual(len(calls), 1)
        cursor = Cursor(self.db)
        cursor.execute(calls[0].args[0].value, (1,))
        assignment = next(n for n in ast.walk(node) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "report_type" for t in n.targets))
        value = eval(compile(ast.Expression(assignment.value), "legacy-report-type", "eval"), {"cursor": cursor})
        self.assertEqual(value, "Follow-up Screening")


if __name__ == "__main__":
    unittest.main()
