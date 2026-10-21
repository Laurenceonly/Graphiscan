"""Back up the local pilot and optionally rehearse SQL restore in a new database.

Run while uploads and record edits are paused. Private output stays in the
Git-ignored .local-backups directory. Never prints configuration or row values.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from datetime import datetime, timezone
import zipfile

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
sys.path.insert(0, str(APP))
os.chdir(APP)

import mysql.connector
from config import DB_CONFIG


def quote_identifier(value):
    return "`" + value.replace("`", "``") + "`"


def option_value(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace(
        "\n", "\\n"
    ).replace("\r", "\\r") + '"'


def fingerprints(connection):
    cursor = connection.cursor()
    cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
    tables = [row[0] for row in cursor.fetchall()]
    result = {}
    for table in tables:
        cursor.execute("SHOW CREATE TABLE " + quote_identifier(table))
        schema_hash = hashlib.sha256(cursor.fetchone()[1].encode()).hexdigest()
        cursor.execute("SELECT * FROM " + quote_identifier(table))
        # Compare content without putting private rows in reports or tool output.
        hashes = sorted(hashlib.sha256(repr(row).encode()).hexdigest() for row in cursor)
        result[table] = {
            "rows": len(hashes),
            "schema_sha256": schema_hash,
            "sha256": hashlib.sha256("".join(hashes).encode()).hexdigest(),
        }
    cursor.close()
    return result


def file_details(path):
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    return {"bytes": path.stat().st_size, "sha256": digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-restore", action="store_true")
    parser.add_argument("--mysql-bin", type=Path, default=Path("C:/xampp/mysql/bin"))
    args = parser.parse_args()
    backup_root = ROOT / ".local-backups"
    subprocess.run(["git", "check-ignore", "--quiet", str(backup_root / "probe.sql")],
                   cwd=ROOT, check=True)
    destination = backup_root / ("checkpoint-" + datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3))
    destination.mkdir(parents=True)
    print("Private backup directory created.", flush=True)
    options = destination / "client.cnf"
    connection = None
    restore_connection = None
    scratch = "graphiscan_restore_check_" + secrets.token_hex(8)
    created_scratch = False
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        baseline = fingerprints(connection)
        connection.rollback()
        client_options = {"host": DB_CONFIG.get("host", "localhost"),
                          "port": DB_CONFIG.get("port", 3306),
                          "user": DB_CONFIG["user"], "password": DB_CONFIG.get("password", "")}
        options.write_text("[client]\n" + "".join(
            key + "=" + option_value(value) + "\n" for key, value in client_options.items()),
            encoding="utf-8")
        sql = destination / "database.sql"
        with sql.open("wb") as output:
            subprocess.run([str(args.mysql_bin / "mysqldump.exe"),
                            "--defaults-extra-file=" + str(options),
                            "--single-transaction", "--quick", "--hex-blob",
                            "--skip-lock-tables",
                            DB_CONFIG["database"]], stdout=output,
                           stderr=subprocess.DEVNULL, check=True, timeout=300)
        if not sql.stat().st_size:
            raise RuntimeError("Empty database dump")
        tracked = subprocess.check_output(["git", "ls-files", "-z", "--cached",
                                           "--others", "--exclude-standard"], cwd=ROOT)
        files = {ROOT / os.fsdecode(name) for name in tracked.split(b"\0") if name}
        for private in [APP / "config.py", APP / ".env", ROOT / ".env"]:
            if private.is_file():
                files.add(private)
        for directory in [APP / "static/uploads", APP / "model"]:
            if directory.exists():
                files.update(p for p in directory.rglob("*") if p.is_file())
        archive = destination / "project-and-private-assets.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(files):
                if path.is_file():
                    bundle.write(path, path.relative_to(ROOT))
        with zipfile.ZipFile(archive) as bundle:
            if bundle.testzip() is not None:
                raise RuntimeError("Archive integrity check failed")
        restored = False
        if args.verify_restore:
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE " + quote_identifier(scratch))
            created_scratch = True
            cursor.close()
            print("Restoring into an isolated temporary database.", flush=True)
            with sql.open("rb") as source:
                subprocess.run([str(args.mysql_bin / "mysql.exe"),
                                "--defaults-extra-file=" + str(options),
                                "--database=" + scratch], stdin=source,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               check=True, timeout=300)
            restore_connection = mysql.connector.connect(**{**DB_CONFIG, "database": scratch})
            restored = fingerprints(restore_connection) == baseline
            if not restored:
                raise RuntimeError("Restored table content differs from baseline")
        manifest = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
                    "tables": baseline, "archive_integrity_passed": True,
                    "database_restore_verified": restored,
                    "limitation": "Pause application writes for a coherent database/image backup.",
                    "files": {p.name: file_details(p) for p in [sql, archive]}}
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print("Backup complete; archive integrity passed; restored content verified: "
              + str(restored) + "; tables: " + str(len(baseline)), flush=True)
        print("Output: " + str(destination.relative_to(ROOT)), flush=True)
    finally:
        try:
            if restore_connection:
                restore_connection.close()
            if connection:
                if created_scratch:
                    # Only this invocation's randomly named, newly created database.
                    cursor = connection.cursor()
                    cursor.execute("DROP DATABASE " + quote_identifier(scratch))
                    cursor.close()
                connection.close()
        finally:
            options.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Connection/CLI errors may contain credentials or private record text.
        print("Backup did not complete (" + type(error).__name__
              + "; code=" + str(getattr(error, "errno", None))
              + "). Review local setup; private error details suppressed.", file=sys.stderr)
        sys.exit(1)
