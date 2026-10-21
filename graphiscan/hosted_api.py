"""Production composition for the hosted v1 API.

Serves the Supabase API and its privately provisioned model runtime.
The Vue admin is deployed separately. Legacy MySQL routes are not mounted.
"""

import os
import re
from urllib.parse import urlsplit

from flask import Flask
from flask_cors import CORS

from api_v1 import install_api_v1
from v1_backend import SupabasePostgresBackend, backend_from_environment


def _allowed_origins(environ):
    """Return only explicit HTTPS frontend origins; fail closed on malformed input."""
    raw = environ.get("GRAPHISCAN_CORS_ALLOWED_ORIGINS", "")
    origins = []
    for value in (part.strip() for part in raw.split(",")):
        if not value:
            continue
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or "*" in parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise RuntimeError("CORS origins must be explicit HTTPS origins")
        origin = f"https://{parsed.netloc}"
        if origin not in origins:
            origins.append(origin)
    if not origins:
        raise RuntimeError("Configure at least one HTTPS frontend origin")
    return origins


def create_app(environ=None):
    environ = os.environ if environ is None else environ
    # Signatures must survive requests reaching different instances or workers.
    if not re.fullmatch(r"[a-fA-F0-9]{64}", environ.get("GRAPHISCAN_V1_CURSOR_SECRET", "")):
        raise RuntimeError("Configure the hosted pagination signing secret")
    origins = _allowed_origins(environ)
    backend = backend_from_environment(environ)
    if not isinstance(backend, SupabasePostgresBackend):
        raise RuntimeError("Configure the hosted Supabase adapter")
    if backend.password_service is None:
        raise RuntimeError("Configure the separate password writer")
    # Admin-only preparation can explicitly omit inference. Screening deployments
    # must validate their private manifest and artifacts before accepting traffic.
    if environ.get("GRAPHISCAN_REQUIRE_MODEL", "true") != "false":
        uploads = backend.screening_upload_service
        if uploads.runtime is None or uploads.storage is None:
            raise RuntimeError("Configure the pinned model runtime and private Storage")
    app = Flask(__name__, static_folder=None)
    CORS(
        app,
        resources={r"/api/v1/*": {
            "origins": origins,
            "allow_headers": ["Authorization", "Content-Type", "Idempotency-Key"],
            "methods": ["GET", "POST", "PATCH", "OPTIONS"],
            "max_age": 600,
        }},
        supports_credentials=False,
    )
    install_api_v1(app, backend)
    return app
