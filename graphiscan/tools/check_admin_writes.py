"""Exercise admin writes against a disposable schema with fictional data only.

Requires the admin Vite server on 5175 with VITE_API_ORIGIN=http://127.0.0.1:5001.
Copies current table definitions, never source rows. Always drops its own database.
"""

import argparse
import logging
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
sys.path.insert(0, str(APP))
os.chdir(APP)

import mysql.connector
from werkzeug.serving import make_server, WSGIRequestHandler
import app as application
from backup_local import fingerprints, quote_identifier

# Fictional fixture credentials, valid only in this invocation's disposable DB.
PASSWORD = "Synthetic!2026Admin"


class QuietHandler(WSGIRequestHandler):
    def log(self, *args, **kwargs):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phone', action='store_true', help='Run browser writes at a 390px viewport')
    args = parser.parse_args()
    source_config = dict(application.DB_CONFIG)
    scratch = "graphiscan_write_check_" + secrets.token_hex(8)
    source = mysql.connector.connect(**source_config)
    created = False
    server = None
    isolated = None
    cli = None
    baseline = fingerprints(source)
    source.rollback()
    try:
        cursor = source.cursor()
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        tables = [r[0] for r in cursor.fetchall()]
        schemas = []
        for table in tables:
            cursor.execute("SHOW CREATE TABLE " + quote_identifier(table))
            schemas.append(cursor.fetchone()[1])
        cursor.execute("CREATE DATABASE " + quote_identifier(scratch))
        created = True
        cursor.close()
        isolated_config = {**source_config, "database": scratch}
        assert scratch != source_config["database"]
        isolated = mysql.connector.connect(**isolated_config)
        cursor = isolated.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        for schema in schemas:
            cursor.execute(schema)
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        roles = [(1, "Synthetic Admin", "admin", "active"),
                 (2, "Synthetic Teacher", "teacher", "active"),
                 (3, "Synthetic Parent", "parent", "active"),
                 (4, "Synthetic Other Parent", "parent", "active"),
                 (5, "Synthetic Pending Approve", "guest", "pending"),
                 (6, "Synthetic Pending Reject", "guest", "pending")]
        for uid, name, role, status in roles:
            cursor.execute("INSERT INTO users (user_id,fullname,email,password,role,account_status) "
                           "VALUES (%s,%s,%s,%s,%s,%s)",
                           (uid, name, f"fixture{uid}@example.invalid", application.hash_password(PASSWORD), role, status))
        isolated.commit()
        cursor.close()
        # This module/process alone changes configuration; the normal server is untouched.
        application.DB_CONFIG = isolated_config
        application.app.logger.disabled = True
        logging.getLogger("werkzeug").disabled = True
        client = application.app.test_client()
        application.ADMIN_TOKENS["synthetic-write-check"] = {"user_id": 1, "role": "admin"}
        headers = {"Authorization": "Bearer synthetic-write-check"}
        count = 0

        def post(route, data, status=200):
            nonlocal count
            response = client.post("/api/admin/" + route, json=data, headers=headers)
            assert response.status_code == status, f"Unexpected status for {route}: {response.status_code}"
            count += 1
            return response.get_json()

        for uid, action in [(5, "approve"), (6, "reject"), (5, "disable"), (5, "restore")]:
            post(f"users/{uid}/{action}", {})
            cursor = isolated.cursor()
            cursor.execute("SELECT account_status FROM users WHERE user_id=%s", (uid,))
            expected = {"approve": "active", "reject": "rejected", "disable": "disabled", "restore": "active"}[action]
            assert cursor.fetchone()[0] == expected, "Status update did not persist"
            isolated.rollback()
            cursor.close()
        post("users/1/disable", {}, 400)
        post("users/1/delete", {"confirmation_text": "DELETE", "admin_password": PASSWORD}, 400)
        post("users/add", {"fullname": "Duplicate", "email": "fixture1@example.invalid",
                          "role": "guest", "password": PASSWORD, "confirm_password": PASSWORD}, 400)
        # Test cascade cleanup with a file created inside this invocation's temp folder.
        with tempfile.TemporaryDirectory(prefix="admin-write-", dir=ROOT / ".local-tools") as temp:
            fake_image = Path(temp) / "synthetic-sample.txt"
            fake_image.write_text("Fictional deletion fixture", encoding="utf-8")
            cursor = isolated.cursor()
            cursor.execute("INSERT INTO students (fullname,age,grade_level,teacher_id,parent_id) VALUES ('Cascade Fixture',8,'Grade 2',2,3)")
            student_id = cursor.lastrowid
            cursor.execute("INSERT INTO handwriting_samples (student_id,teacher_id,image_path) VALUES (%s,2,%s)", (student_id, str(fake_image)))
            sample_id = cursor.lastrowid
            cursor.execute("INSERT INTO results (sample_id,classification,dysgraphia_probability,confidence_score,analysis_summary,recommendation) VALUES (%s,'Normal',10,90,'','')", (sample_id,))
            result_id = cursor.lastrowid
            cursor.execute("INSERT INTO validations (result_id) VALUES (%s)", (result_id,))
            cursor.execute("INSERT INTO reports (student_id,result_id) VALUES (%s,%s)", (student_id, result_id))
            isolated.commit()
            cursor.close()
            post(f"students/{student_id}/delete", {"confirmation_text": "WRONG", "admin_password": PASSWORD}, 400)
            post(f"students/{student_id}/delete", {"confirmation_text": "DELETE", "admin_password": "wrong-fixture-password"}, 403)
            result = post(f"students/{student_id}/delete", {"confirmation_text": "DELETE", "admin_password": PASSWORD})
            assert result["deleted_summary"] == {"samples": 1, "results": 1, "reports": 1, "validations": 1}
            assert not fake_image.exists(), "Synthetic image was not deleted"
        print(f"Isolated API write checks: {count} PASS; cascade file cleanup PASS", flush=True)
        server = make_server("127.0.0.1", 5001, application.app, threaded=True, request_handler=QuietHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        npx = shutil.which("npx.cmd") or shutil.which("npx")
        assert npx, "npx is required"
        cli = [npx, "--yes", "--package", "@playwright/cli", "playwright-cli", "-s=adminwrites"]
        subprocess.run(cli + ["close"], cwd=ROOT, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(cli + ["open", "http://127.0.0.1:5175/login", "--headed"], cwd=ROOT, check=True, timeout=90, stdout=subprocess.DEVNULL)
        if args.phone:
            subprocess.run(cli + ["resize", "390", "844"], cwd=ROOT, check=True, timeout=30, stdout=subprocess.DEVNULL)
        subprocess.run(cli + ["run-code", "--filename", str(APP / "tools/admin_write_browser.js")], cwd=ROOT, check=True, timeout=180)
        cursor = isolated.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        assert cursor.fetchone()[0] >= 12, "Expected mutation audit entries"
        cursor.execute("SELECT COUNT(*) FROM students")
        assert cursor.fetchone()[0] == 0, "Browser student deletion did not persist"
        cursor.execute("SELECT COUNT(*) FROM users WHERE email='browser-guest@example.invalid'")
        assert cursor.fetchone()[0] == 0, "Browser account deletion did not persist"
        cursor.close()
        print("Isolated database persistence and audit checks: PASS", flush=True)
    finally:
        if cli:
            try:
                subprocess.run(cli + ["close"], cwd=ROOT, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.SubprocessError:
                print("Synthetic browser cleanup needs review.", flush=True)
        if server:
            server.shutdown()
            server.server_close()
        if isolated:
            isolated.close()
        application.DB_CONFIG = source_config
        if created:
            cursor = source.cursor()
            cursor.execute("DROP DATABASE " + quote_identifier(scratch))
            cursor.close()
            print("Disposable database removed.", flush=True)
        source.rollback()
        unchanged = fingerprints(source) == baseline
        source.close()
        print("Source database unchanged: " + str(unchanged), flush=True)
        assert unchanged, "Source database changed during check; investigate concurrent activity"


if __name__ == "__main__":
    (ROOT / ".local-tools").mkdir(exist_ok=True)
    try:
        main()
    except Exception as error:
        # Do not print DB errors/configuration or subprocess arguments.
        print("Admin write check failed: " + type(error).__name__, flush=True)
        sys.exit(1)
