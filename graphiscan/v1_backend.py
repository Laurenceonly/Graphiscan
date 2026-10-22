"""Opt-in Supabase Auth + PostgreSQL access adapter; no configuration is logged.

Supabase /auth/v1/user authenticates the exact token remotely. Only after that
successful verification do we decode its signed claims for subject/session IDs.
This is deliberately not an offline JWT verifier. PostgreSQL additionally checks
durable session existence, revocation and the current profile security floor.
"""

import base64
import json
import math
import os
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

import requests

from api_v1 import (AccessState, BackendUnavailable, Grant, Identity,
                    InvalidSession, UnavailableBackend)


SNAPSHOT_SQL = (Path(__file__).parent / "db/postgres/access_snapshot.sql").read_text(encoding="utf-8")


class SupabaseIdentityVerifier:
    def __init__(self, url, publishable_key, *, get=None, now=None):
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
                parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            raise ValueError("A trusted HTTPS Supabase project origin is required")
        if not publishable_key or not publishable_key.startswith("sb_publishable_"):
            raise ValueError("A Supabase publishable key is required")
        self.origin = url.rstrip("/")
        self.key = publishable_key
        self.get = get if get is not None else requests.get
        self.now = now if now is not None else time.time

    def authenticate(self, bearer):
        if not isinstance(bearer, str) or len(bearer) > 16384 or bearer.count(".") != 2:
            raise InvalidSession()
        try:
            response = self.get(self.origin + "/auth/v1/user",
                                headers={"apikey": self.key, "Authorization": "Bearer " + bearer},
                                timeout=(3.05, 5), allow_redirects=False)
        except requests.RequestException:
            raise BackendUnavailable() from None
        try:
            if response.status_code in (401, 403):
                raise InvalidSession()
            if response.status_code != 200:
                raise BackendUnavailable()
            try:
                user = response.json()
            except (ValueError, TypeError):
                raise BackendUnavailable() from None
            if not isinstance(user, dict) or not isinstance(user.get("id"), str):
                raise BackendUnavailable()
            try:
                # Safe to interpret only because the trusted provider verified
                # this same bearer above. Never use user_metadata for authorization.
                payload = bearer.split(".")[1]
                claims = json.loads(base64.b64decode(payload + "=" * (-len(payload) % 4),
                                                     altchars=b"-_", validate=True))
                if not isinstance(claims, dict):
                    raise ValueError()
                subject = str(UUID(claims["sub"]))
                session = str(UUID(claims["session_id"]))
                audience = claims.get("aud")
                if not (audience == "authenticated" or
                        isinstance(audience, list) and "authenticated" in audience):
                    raise ValueError()
                if claims.get("iss") != self.origin + "/auth/v1" or str(UUID(user["id"])) != subject:
                    raise ValueError()
                now = self.now()
                for key in ("exp", "iat"):
                    value = claims[key]
                    if type(value) not in (int, float) or not math.isfinite(value):
                        raise ValueError()
                if claims["exp"] <= now or claims["iat"] > now or claims["exp"] <= claims["iat"]:
                    raise ValueError()
                if "nbf" in claims:
                    value = claims["nbf"]
                    if type(value) not in (int, float) or not math.isfinite(value) or value > now:
                        raise ValueError()
            except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
                raise InvalidSession() from None
            return Identity(subject, session)
        finally:
            response.close()


class PostgresAccessRepository:
    def __init__(self, connect):
        self.connect = connect

    def load_access(self, identity):
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(SNAPSHOT_SQL, {"user_id": identity.user_id, "session_id": identity.session_id})
                    row = cursor.fetchone()
            if row is None:
                raise BackendUnavailable()
            if row["session_valid"] is not True:
                raise InvalidSession()
            if row["user_id"] is None:
                return None
            if type(row["must_change_password"]) is not bool:
                raise BackendUnavailable()
            return AccessState(
                user_id=row["user_id"], full_name=row["full_name"], role=row["role"],
                account_status=row["account_status"], must_change_password=row["must_change_password"],
                required_agreement_version=row["required_agreement_version"],
                accepted_agreement_version=row["accepted_agreement_version"],
                grants=tuple(Grant(g["permission"], g["school_id"]) for g in row["grants"]),
                school_ids=tuple(row["school_ids"]),
            )
        except (InvalidSession, BackendUnavailable):
            raise
        except Exception:
            # Includes driver errors with DSNs/SQL details; never cross API boundary.
            raise BackendUnavailable() from None


class SupabasePostgresBackend:
    def __init__(self, verifier, repository, password_service=None, privacy_service=None):
        self.verifier, self.repository = verifier, repository
        self.password_service = password_service
        self.privacy_service = privacy_service
        self.session_service = None

    def authenticate(self, bearer):
        return self.verifier.authenticate(bearer)

    def load_access(self, identity):
        # Guard invokes this immediately after authenticate, before any handler.
        return self.repository.load_access(identity)


def backend_from_environment(environ=None):
    """No network/DB connection on startup. Explicit opt-in; partial setup denies.

    Runtime database role needs only SELECT on the snapshot's six public tables
    and EXECUTE on the restricted session function installed by 005. Database
    credentials never go to Auth; session/password operations send only account
    credentials supplied for that operation. Existing MySQL configuration remains independent.
    """
    env = os.environ if environ is None else environ
    if env.get("GRAPHISCAN_V1_BACKEND", "") != "supabase-postgres":
        return UnavailableBackend()
    try:
        verifier = SupabaseIdentityVerifier(env.get("GRAPHISCAN_V1_SUPABASE_URL", ""),
                                            env.get("GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY", ""))
        dsn = env["GRAPHISCAN_V1_DATABASE_URL"]
        if not dsn:
            raise ValueError()
        import psycopg
        from psycopg.rows import dict_row
        # Validate syntax now without connecting; do not echo DSN on error.
        psycopg.conninfo.conninfo_to_dict(dsn)

        def connect():
            return psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5,
                                   sslmode="verify-full", application_name="graphiscan-v1-access",
                                   options="-c timezone=UTC -c statement_timeout=5000 -c default_transaction_read_only=on")

        password_service = None
        writer_dsn = env.get("GRAPHISCAN_V1_PASSWORD_DATABASE_URL", "")
        if writer_dsn:
            # Explicit opt-in with separate credentials. Never reuse the reader
            # or fall back to an owner/service key for reviewed mutations.
            writer_info = psycopg.conninfo.conninfo_to_dict(writer_dsn)
            if writer_info.get("user", "").split(".")[0] != "graphiscan_password_writer":
                raise ValueError()
            from v1_password import PasswordService, PostgresPasswordRepository, SupabasePasswordProvider

            def writer_connect():
                connection = psycopg.connect(writer_dsn, row_factory=dict_row, connect_timeout=5,
                                             sslmode="verify-full", application_name="graphiscan-v1-password",
                                             options="-c timezone=UTC -c statement_timeout=5000 -c lock_timeout=3000")
                try:
                    # Poolers may not retain startup options. Establish these
                    # session settings explicitly before any function invocation.
                    connection.execute("SET SESSION TIME ZONE 'UTC'")
                    connection.execute("SET SESSION statement_timeout = '5s'")
                    connection.execute("SET SESSION lock_timeout = '3s'")
                    connection.commit()
                    return connection
                except Exception:
                    connection.close()
                    raise

            password_service = PasswordService(SupabasePasswordProvider(verifier),
                                               PostgresPasswordRepository(writer_connect))
        from v1_privacy import PrivacyService
        privacy_service = PrivacyService(connect, password_service.repository if password_service else None)
        backend = SupabasePostgresBackend(verifier, PostgresAccessRepository(connect), password_service, privacy_service)
        admin_dsn = env.get("GRAPHISCAN_V1_ADMIN_DATABASE_URL", "")
        if admin_dsn:
            admin_info = psycopg.conninfo.conninfo_to_dict(admin_dsn)
            if admin_info.get("user", "").split(".")[0] != "graphiscan_admin_writer":
                raise ValueError()
            from v1_admin_writes import AdminWriteService, PostgresAdminWriteRepository

            def admin_connect():
                connection = psycopg.connect(admin_dsn, row_factory=dict_row, connect_timeout=5,
                                             sslmode="verify-full", application_name="graphiscan-v1-admin-write",
                                             options="-c timezone=UTC -c statement_timeout=5s -c lock_timeout=3s")
                try:
                    connection.execute("SET SESSION TIME ZONE 'UTC'")
                    connection.execute("SET SESSION statement_timeout = '5s'")
                    connection.execute("SET SESSION lock_timeout = '3s'")
                    connection.commit()
                    return connection
                except Exception:
                    connection.close()
                    raise

            backend.admin_write_service = AdminWriteService(PostgresAdminWriteRepository(admin_connect))
            auth_secret = env.get('GRAPHISCAN_V1_SUPABASE_AUTH_SECRET_KEY', '')
            if auth_secret:
                from v1_account_issuance import AccountIssuanceService, SupabaseAccountProvider
                backend.account_issuance_service = AccountIssuanceService(
                    PostgresAdminWriteRepository(admin_connect), SupabaseAccountProvider(verifier, auth_secret))
        from v1_sessions import SessionService
        from v1_password import SupabasePasswordProvider
        from v1_admin_lifecycle import AdminLifecycleService
        from v1_admin_writes import PostgresAdminWriteRepository
        issuer = getattr(backend, 'account_issuance_service', None)
        backend.admin_lifecycle_service = AdminLifecycleService(PostgresAdminWriteRepository(connect),
            getattr(backend, 'admin_write_service', None).repository if getattr(backend, 'admin_write_service', None) else None,
            issuer.provider if issuer else None, SupabasePasswordProvider(verifier))
        backend.session_service = SessionService(backend,SupabasePasswordProvider(verifier),
                                                 password_service.repository if password_service else None)
        from v1_directory import DirectoryService
        cursor_options = {}
        cursor_secret = env.get("GRAPHISCAN_V1_CURSOR_SECRET", "")
        if cursor_secret:
            cursor_key = bytes.fromhex(cursor_secret)
            if len(cursor_key) != 32:
                raise ValueError()
            cursor_options["cursor_key"] = cursor_key
        backend.directory_service = DirectoryService(connect, **cursor_options)
        from v1_admin_reads import AdminReadService
        backend.admin_read_service = AdminReadService(connect, **cursor_options)
        from v1_screenings import ScreeningReadService
        backend.screening_read_service = ScreeningReadService(connect, **cursor_options)
        from v1_screening_writes import ScreeningWriteService
        backend.screening_write_service = ScreeningWriteService(password_service.repository if password_service else None)
        from v1_uploads import ScreeningUploadService
        from v1_models import runtime_from_manifest
        from v1_storage import storage_from_environment
        runtime=None
        if env.get('GRAPHISCAN_V1_MODEL_MANIFEST'):
            try:runtime=runtime_from_manifest(env['GRAPHISCAN_V1_MODEL_MANIFEST'])
            except Exception:runtime=None
        backend.screening_upload_service=ScreeningUploadService(connect,
            password_service.repository if password_service else None,runtime,storage_from_environment(env),**cursor_options)
        from v1_directory_writes import DirectoryWriteService
        backend.directory_write_service = DirectoryWriteService(password_service.repository if password_service else None)
        from v1_assignment_options import AssignmentOptionsService
        backend.assignment_options_service = AssignmentOptionsService(connect, **cursor_options)
        return backend
    except Exception:
        return UnavailableBackend()
