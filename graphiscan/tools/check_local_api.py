"""Read-only live-database API baseline; not a real login/browser test.

Uses existing active role IDs with temporary tokens in this process only.
Prints endpoint names/statuses, never tokens, accounts, or response records.
"""

import logging
import os
from pathlib import Path
import secrets
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
os.chdir(APP)

from app import ADMIN_TOKENS, USER_TOKENS, app, get_db_connection


def main():
    # Flask exception logging can include private query/configuration details.
    app.logger.disabled = True
    logging.getLogger("werkzeug").disabled = True
    client = app.test_client()
    failures = []

    def check(label, route, expected, headers=None):
        response = client.get(route, headers=headers or {})
        passed = response.status_code == expected
        print(label + ": " + str(response.status_code) + " " + ("PASS" if passed else "FAIL"),
              flush=True)
        if not passed:
            failures.append(label)
        return response

    check("health", "/api/user/health", 200)
    routes = {
        "admin": ["/api/admin/dashboard", "/api/admin/users", "/api/admin/students",
                  "/api/admin/students/progress", "/api/admin/results", "/api/admin/audit-logs"],
        "teacher": ["/api/user/teacher/students", "/api/user/teacher/results"],
        "parent": ["/api/user/parent/results"],
        "expert": ["/api/user/expert/results"],
    }
    for role_routes in routes.values():
        for route in role_routes:
            check("unauthenticated " + route, route, 401)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, role FROM users WHERE account_status = 'active'")
        available = {}
        for row in cursor.fetchall():
            available.setdefault(row["role"], row)
    finally:
        cursor.close()
        connection.close()

    for role, role_routes in routes.items():
        user = available.get(role)
        if not user:
            print(role + ": SKIP (no active account)", flush=True)
            continue
        token = secrets.token_urlsafe(32)
        tokens = ADMIN_TOKENS if role == "admin" else USER_TOKENS
        tokens[token] = dict(user)
        headers = {"Authorization": "Bearer " + token}
        try:
            for route in role_routes:
                response = check(role + " " + route, route, 200, headers)
                data = response.get_json(silent=True) or {}
                # Also exercise a populated detail endpoint when one exists.
                if route == "/api/admin/results" and data.get("results"):
                    result_id = data["results"][0]["result_id"]
                    check("admin result detail", "/api/admin/results/" + str(result_id), 200, headers)
                if route == "/api/admin/students" and data.get("students"):
                    student_id = data["students"][0]["student_id"]
                    check("admin student progress detail", "/api/admin/students/"
                          + str(student_id) + "/progress", 200, headers)
            if role in ("teacher", "parent", "expert"):
                other = "/api/user/parent/results" if role == "teacher" else "/api/user/teacher/results"
                check(role + " wrong-role access", other, 403, headers)
        finally:
            tokens.pop(token, None)
    print("Baseline complete; failures: " + str(len(failures)), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("Baseline failed (" + type(error).__name__
              + "); private error details suppressed.", file=sys.stderr)
        sys.exit(1)
