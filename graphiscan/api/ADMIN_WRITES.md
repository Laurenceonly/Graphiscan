# Hosted account updates

`PATCH /api/v1/accounts/{user_id}` is implemented in the v1 source. It supports full-name, role, status, school-membership, and explicit permission-grant updates. Every request requires the current active session, completed onboarding, a global `accounts.manage` grant, and `expected_revision`. Replacing grants additionally requires `permissions.manage` for the applicable scope. The database function rechecks these conditions, limits grant scope to the actor's grants, protects the caller's own role/status/scope, protects the last active administrator, increments revisions, invalidates affected sessions, and writes an audit row in the same transaction.

## Hosted schema status

The user applied `db/postgres/017_account_management.sql`. A restricted read-only check confirmed the function and all catalog/privilege checks. **Do not rerun migration 017.** It creates a `NOLOGIN`, `NOINHERIT`, non-bypass `graphiscan_admin_writer` role and grants it only the account-update function. It also adds account revision to the protected admin-list projection. It does not provision Auth users, reset passwords, or alter existing account data.

## Finish private writer setup

After the migration succeeds, create a new password for the writer privately in SQL Editor and store it only in the local server environment:

```sql
ALTER ROLE graphiscan_admin_writer WITH LOGIN PASSWORD 'REPLACE_WITH_A_NEW_PRIVATE_PASSWORD';
```

From `graphiscan/`, run the helper in your own interactive terminal after setting that role password:

```powershell
..\.venv\Scripts\python.exe tools/configure_v1_admin_writer.py
```

Enter the new database-role password at its hidden prompt. The helper derives `GRAPHISCAN_V1_ADMIN_DATABASE_URL` from the existing reader's trusted host, pooler suffix and TLS settings, writes only that separate environment setting, and refuses to overwrite an existing value. It does not connect or echo the password. The adapter requires the exact `graphiscan_admin_writer` user, TLS hostname verification, UTC, a five-second statement timeout, and a three-second lock timeout. Restart Flask after the private configuration is set. Do not use the reader, password writer, Supabase service key, or browser-exposed settings for this function.

Verify the setup using read-only checks:

```powershell
..\.venv\Scripts\python.exe tools/check_v1_admin_writer.py --connect
```

The default invocation without `--connect` performs no network access. With it, the checker uses the restricted reader for catalog checks and, when configured, starts an explicit read-only transaction on the writer for login/settings checks. It prints only boolean results and never invokes the account-update function. A `migration-required` result means 017 is absent; `writer-configuration-required` means the catalog passed but private writer setup remains. Only `admin-writer-setup-passed` establishes the checked installation, grants and connection settings. It does not prove authenticated account mutation behavior.

Latest actual hosted check (2026-10-21): migration017 installation, all catalog/privilege checks, and the separate writer connection settings passed. Overall status is `admin-writer-setup-passed`. The check was read-only and changed no account or other records. Restart Flask after configuration before using hosted account updates.

## Current limits

The hosted Users page supports editing name, role, and status. The API also accepts school memberships and permission-grant replacement. Account creation and temporary-password reset remain unimplemented; no service-role credential or test user was created for this work. Full role workflows, database cutover, and hosted writes remain unverified. SQL and API checks use fictional, isolated data only.
