"""Privately derive the writer URI from the existing verified reader URI.

Interactive local setup only. Does not connect, print a URI or change the reader.
"""
import getpass
import json
import sys
import warnings
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from dotenv import dotenv_values, set_key

ENV_PATH = Path(__file__).resolve().parents[1] / '.env'


def writer_uri(reader_uri, password, role='graphiscan_password_writer'):
    if role not in {'graphiscan_password_writer', 'graphiscan_admin_writer'}:
        raise ValueError('Unsupported writer role.')
    if not isinstance(password, str) or not password:
        raise ValueError('A writer password is required.')
    uri = urlsplit(reader_uri)
    username = unquote(uri.username or '')
    prefix = 'graphiscan_api_reader'
    if (uri.scheme not in ('postgres', 'postgresql') or not uri.hostname or
            not uri.path.strip('/') or not (username == prefix or username.startswith(prefix + '.')) or
            uri.fragment):
        raise ValueError('A configured PostgreSQL reader URI is required.')
    # Preserve project suffix for the session pooler, plus the complete trusted
    # host/port/query (including sslrootcert). Encode the new password exactly once.
    user = role + username[len(prefix):]
    host = '[' + uri.hostname + ']' if ':' in uri.hostname else uri.hostname
    port = ':' + str(uri.port) if uri.port is not None else ''
    netloc = quote(user, safe='') + ':' + quote(password, safe='') + '@' + host + port
    return urlunsplit((uri.scheme, netloc, uri.path, uri.query, ''))


def main(role='graphiscan_password_writer', env_key='GRAPHISCAN_V1_PASSWORD_DATABASE_URL'):
    if (role, env_key) not in {
            ('graphiscan_password_writer', 'GRAPHISCAN_V1_PASSWORD_DATABASE_URL'),
            ('graphiscan_admin_writer', 'GRAPHISCAN_V1_ADMIN_DATABASE_URL')}:
        raise ValueError('Unsupported writer configuration.')
    if len(sys.argv) != 1 or not sys.stdin.isatty():
        print(json.dumps({'status': 'blocked', 'reason': 'Use an interactive terminal without arguments.'}))
        return 2
    try:
        # Parse only this file; never print it or expand arbitrary env references.
        values = dotenv_values(ENV_PATH, interpolate=False)
        reader = values.get('GRAPHISCAN_V1_DATABASE_URL', '')
        if values.get(env_key):
            print(json.dumps({'status': 'blocked', 'reason': 'Writer configuration already exists; no changes made.'}))
            return 2
        # Validate before prompting. No credentials leave this process/file.
        writer_uri(reader, 'synthetic-validation-only', role)
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            password = getpass.getpass('New database WRITER password (hidden): ')
        uri = writer_uri(reader, password, role)
        result = set_key(ENV_PATH, env_key, uri, quote_mode='always')
        password = uri = None
        if result[0] is not True:
            raise ValueError()
        print(json.dumps({'status': 'writer-configuration-saved', 'connection_tested': False,
                          'reader_changed': False}))
        return 0
    except (Exception, KeyboardInterrupt):
        print(json.dumps({'status': 'not-confirmed', 'reason': 'Private setup did not complete; no connection attempted.'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
