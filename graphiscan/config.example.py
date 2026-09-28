"""Example local configuration. Copy to config.py and supply values via .env."""

import os

from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.environ.get("GRAPHISCAN_DB_HOST", "localhost"),
    "user": os.environ["GRAPHISCAN_DB_USER"],
    "password": os.environ["GRAPHISCAN_DB_PASSWORD"],
    "database": os.environ["GRAPHISCAN_DB_NAME"],
}

SECRET_KEY = os.environ["GRAPHISCAN_SECRET_KEY"]
