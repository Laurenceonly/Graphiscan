"""Preserve stopped XAMPP MySQL files; not a verified SQL restore backup."""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('C:/xampp/mysql/data')


def ensure_stopped():
    result = subprocess.check_output(['tasklist.exe', '/FI', 'IMAGENAME eq mysqld.exe', '/FO', 'CSV', '/NH'], text=True)
    if any(row and row[0].lower() == 'mysqld.exe' for row in csv.reader(io.StringIO(result))):
        raise RuntimeError('MySQL must be stopped before an offline copy')


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def fingerprint(directory):
    return {str(path.relative_to(directory)): {'bytes': path.stat().st_size, 'sha256': digest(path)}
            for path in sorted(directory.rglob('*')) if path.is_file()}


def main():
    ensure_stopped()
    subprocess.run(['git', 'check-ignore', '--quiet', '.local-backups/probe.sql'], cwd=ROOT, check=True)
    baseline = fingerprint(SOURCE)
    if not baseline:
        raise RuntimeError('Empty source directory')
    ensure_stopped()
    target = ROOT / '.local-backups' / ('mysql-offline-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + secrets.token_hex(3))
    target.mkdir(parents=True, exist_ok=False)
    shutil.copytree(SOURCE, target / 'data')
    shutil.copy2('C:/xampp/mysql/bin/my.ini', target / 'my.ini')
    ensure_stopped()
    if fingerprint(SOURCE) != baseline or fingerprint(target / 'data') != baseline:
        raise RuntimeError('Source changed or copied files differ; snapshot is not verified')
    manifest = {'source': str(SOURCE), 'files': baseline, 'copy_hashes_verified': True,
                'database_restore_verified': False, 'limitation': 'Offline file preservation only; no SQL restore or server recovery verification.'}
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'offline-copy-verified', 'files': len(baseline),
                      'bytes': sum(item['bytes'] for item in baseline.values()),
                      'path': str(target.relative_to(ROOT)), 'database_restore_verified': False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'offline-copy-failed', 'category': type(error).__name__}))
        sys.exit(1)
