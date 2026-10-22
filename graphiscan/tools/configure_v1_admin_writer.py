"""Save the separate account-writer URI using a local hidden password prompt."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.configure_v1_password_writer import main

if __name__ == '__main__':
    raise SystemExit(main(role='graphiscan_admin_writer', env_key='GRAPHISCAN_V1_ADMIN_DATABASE_URL'))
