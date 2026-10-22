"""Prepare an ignored Render import bundle. Never print secret values or upload it."""
import argparse
import json
import os
import re
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values, set_key
from psycopg.conninfo import conninfo_to_dict, make_conninfo


def export(frontend_origin):
    parsed = urlsplit(frontend_origin)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or '*' in parsed.netloc or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise ValueError('Supply the exact HTTPS admin origin.')
    root = Path(__file__).resolve().parents[2]
    source = dotenv_values(root / 'graphiscan' / '.env')
    required = ('GRAPHISCAN_V1_SUPABASE_URL', 'GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY',
                'GRAPHISCAN_V1_SUPABASE_AUTH_SECRET_KEY')
    if any(not source.get(key) for key in required):
        raise ValueError('Local server configuration is incomplete.')
    output = root / '.local-tools' / 'render-private'
    if output.exists():
        raise ValueError('An export bundle already exists; preserve and review it before generating another.')
    roles = {'GRAPHISCAN_V1_DATABASE_URL': 'graphiscan_api_reader',
             'GRAPHISCAN_V1_PASSWORD_DATABASE_URL': 'graphiscan_password_writer',
             'GRAPHISCAN_V1_ADMIN_DATABASE_URL': 'graphiscan_admin_writer'}
    connections = {}
    ca_bytes = None
    fallback = source.get('PGSSLROOTCERT') or os.environ.get('PGSSLROOTCERT')
    default_ca = Path(os.environ.get('APPDATA', str(Path.home()))) / 'postgresql' / 'root.crt'
    for key, role in roles.items():
        info = conninfo_to_dict(source.get(key) or '')
        if info.get('user', '').split('.')[0] != role or not info.get('host') or not info.get('password'):
            raise ValueError('A restricted server database connection is missing.')
        cert = info.get('sslrootcert') or fallback or (str(default_ca) if default_ca.is_file() else 'system')
        if cert != 'system':
            data = Path(cert).read_bytes()
            if b'-----BEGIN CERTIFICATE-----' not in data or b'PRIVATE KEY' in data:
                raise ValueError('The configured database CA file is not a certificate bundle.')
            if ca_bytes is not None and data != ca_bytes:
                raise ValueError('Database connections use different CA bundles; review before exporting.')
            ca_bytes = data
        connections[key] = info
    values = {key: source[key] for key in required}
    for key, info in connections.items():
        info['sslmode'] = 'verify-full'
        info['sslrootcert'] = '/etc/secrets/graphiscan-db-root.crt' if ca_bytes else 'system'
        for local_option in ('sslcert', 'sslkey', 'sslcrl', 'sslcrldir'):
            if info.get(local_option):
                raise ValueError('Client TLS files require a separate reviewed host setup.')
        values[key] = make_conninfo(**info)
    for key in ('GRAPHISCAN_V1_STORAGE_BUCKET', 'GRAPHISCAN_V1_S3_ENDPOINT', 'GRAPHISCAN_V1_S3_REGION',
                'GRAPHISCAN_V1_S3_ACCESS_KEY_ID', 'GRAPHISCAN_V1_S3_SECRET_ACCESS_KEY'):
        if source.get(key):
            values[key] = source[key]
    cursor = source.get('GRAPHISCAN_V1_CURSOR_SECRET') or secrets.token_hex(32)
    if not re.fullmatch(r'[0-9a-fA-F]{64}', cursor):
        raise ValueError('The pagination signing key must contain64 hex characters.')
    values.update(GRAPHISCAN_V1_BACKEND='supabase-postgres', GRAPHISCAN_REQUIRE_MODEL='false',
                  GRAPHISCAN_V1_CURSOR_SECRET=cursor, GRAPHISCAN_CORS_ALLOWED_ORIGINS='https://' + parsed.netloc)
    output.mkdir(parents=True)
    env_file = output / 'admin-api.env'
    env_file.touch()
    for key, value in values.items():
        set_key(str(env_file), key, value)
    if ca_bytes:
        (output / 'graphiscan-db-root.crt').write_bytes(ca_bytes)
    print(json.dumps({'status': 'private-render-bundle-prepared', 'values_printed': False,
                      'configuration_uploaded': False, 'certificate_file_required': ca_bytes is not None,
                      'environment_file': '.local-tools/render-private/admin-api.env'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend-origin', required=True)
    args = parser.parse_args()
    try:
        export(args.frontend_origin)
    except (Exception, KeyboardInterrupt):
        print(json.dumps({'status': 'private-export-not-confirmed', 'private_error_omitted': True,
                          'hint': 'Check complete restricted configuration, CA files, HTTPS origin and absence of an earlier export.'}))
        raise SystemExit(1)
