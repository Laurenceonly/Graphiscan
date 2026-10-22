"""Save the server-only Auth secret locally through a hidden prompt. No network."""
import getpass
import json
import re
import sys
from pathlib import Path

from dotenv import dotenv_values, set_key


def configure():
    if not sys.stdin.isatty():
        raise ValueError()
    env_file = Path(__file__).resolve().parents[1] / '.env'
    field = 'GRAPHISCAN_V1_SUPABASE_AUTH_SECRET_KEY'
    current = dotenv_values(env_file)
    if current.get(field) or not current.get('GRAPHISCAN_V1_SUPABASE_URL'):
        raise ValueError()
    secret = getpass.getpass('Supabase server secret key (hidden): ')
    if not re.fullmatch(r'sb_secret_[A-Za-z0-9_-]{16,256}', secret):
        raise ValueError()
    set_key(str(env_file), field, secret)
    print(json.dumps({'status': 'account-issuance-configuration-saved',
                      'connection_tested': False, 'database_changed': False}))


if __name__ == '__main__':
    try:
        configure()
    except (Exception, KeyboardInterrupt):
        print(json.dumps({'status': 'configuration-not-saved', 'private_error_omitted': True,
                          'hint': 'Use an interactive terminal, a configured project, and an empty Auth secret setting.'}))
        sys.exit(1)
