# Hosted account management

Current evidence (2026-10-22): schema through019 is installed and API/admin are
published. Authorized UI checks created a fictional teacher201 (forced password
change), edited name/synthetic-school membership200, disabled/reactivated200,
and removed the test membership200. Reset dialog is prepared for private issuer
password entry, with no result observed yet; deletion and complete role flows
remain unverified. Do not follow older pending018/019 setup instructions below.

## Current admin completion work

Source now includes current-account detail, school/permission editing,
disable/activate confirmation, temporary-password reset and unused-account
deletion through prepared migration019. See [admin release](ADMIN_RELEASE.md)
for feature evidence, rollout, recovery limitations and deployment order.
Migration019 is not counted installed until a fresh hosted catalog check passes.
The initial generated019 syntax error has been corrected; use the current full
file, whose DDL compiled locally. No live reset/delete has been performed.

## Account creation: source prepared, rollout pending

Actual creation checkpoint (2026-10-22): user-created account after current API replacement; complete read-only reconciliation found1 issuance-marked Auth identity,1 matching application profile and0 Auth-only identities. Creation completion is now observed. First-login password/privacy, role access and live Edit/status behavior remain unverified. No private account details were printed or agent mutations performed. Earlier unavailable/unverified-creation notes below are historical.

Local activation checkpoint (2026-10-22): user saved the server Auth secret privately; backend loads account issuance service. Loopback API5002 is running with health200 and anonymous account-list401; admin preview5173 responds200. The key has not yet been validated by an authenticated provider operation, and no real account was created. Next is private admin sign-in and reviewed account-flow use. No migration or key re-entry is needed at this checkpoint. Earlier missing-key notes below are historical.

Latest rollout (2026-10-22): user applied018; actual restricted read-only checker passed all28 catalog/permission/session checks and confirmed018 installation. **Do not rerun017 or018.** Local server Auth secret is not configured; continue at step2 below, then start/restart the API. Live account creation has not been verified. The earlier unapplied implementation checkpoint below is historical.

`POST /api/v1/accounts` and the hosted **Add user** dialog are implemented in source. Before enabling creation:

1. Review and apply **only** `db/postgres/018_account_issuance.sql` once in Supabase SQL Editor as the schema owner. Migration017 is already installed; do not repeat it.
2. Obtain a server secret key (`sb_secret_…`) for the same Supabase project. From the repository root, run the hidden-prompt helper with a working Python environment containing `python-dotenv`:

   ```powershell
   .\.venv\Scripts\python.exe .\graphiscan\tools\configure_v1_account_issuance.py
   ```

   It saves `GRAPHISCAN_V1_SUPABASE_AUTH_SECRET_KEY` in the ignored server `.env`, refuses to overwrite an existing key, prints no key, and performs no network calls. Do not paste the key in chat or browser/client settings. Existing Auth publishable-key and restricted database writer settings stay separate.
3. Run the existing read-only catalog checker with `--connect`; it now checks migration018 function ownership, fixed search paths, writer grants, denial for other runtime roles/PUBLIC, and protected issuance-table access when018 is present. Restart the Flask API to load the new setting. No setup helper creates a user.

Creation accepts full name, email, role, a temporary password, and school IDs. The admin form offers an optional school from the first100 available schools. New profiles are active, have `must_change_password=true`, and receive no permission grants or privacy acceptance. The existing password and privacy gates apply at first login. An admin issues the credentials privately; creation does not send email. A researcher with global `accounts.manage` cannot create administrators/researchers. Supabase email confirmation is set explicitly for these administrator-issued accounts.

The server commits a durable email/request reservation **before** the single Auth admin call. A completed request UUID returns its existing result; an unfinished UUID/email cannot invoke Auth again. Completion verifies the returned Auth identity against its stored email and provider-controlled issuance marker, then inserts profile, school memberships and audit entry transactionally. Passwords, password hashes and provider keys are never stored in the reservation/audit. No existing Auth identity is attached or overwritten. An Auth-only identity has no application profile and cannot enter the API.

### Interrupted creation

`ACCOUNT_CREATION_PENDING` requires checking the account list and private operator reconciliation. Do not automatically retry provider writes, delete identities, or clear reservations on a timeout. The operator must inspect the reservation and the same-project Auth identity, verify its provider-controlled `graphiscan_issuance_id`, and establish whether profile completion committed. The completion capability can finish the same verified identity under a currently authorized issuing actor/session; its replay returns the stored result. No public recovery route or automated orphan cleanup is implemented. Keep unresolved reservations until reviewed; known provider rejection also remains reserved conservatively.

Implementation evidence for this slice: admin build passed; source/contract review completed. Migration018 has **not** been applied, no real account has been created/edited, and live Auth issuance has not been verified. Follow-up confirmed Python3.11.9 works outside the task sandbox and all five changed Python files parse successfully. The earlier missing-interpreter diagnosis was incorrect: sandbox access restrictions blocked the AppData interpreter. This was a syntax check, not backend/SQL/Auth verification. The existing migration017 installation evidence below is unchanged.

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

The hosted Users page supports editing name, role, and status, plus the prepared account-creation flow above. The update API also accepts school memberships and permission-grant replacement. Edit now keeps uncertain saves gated until a successful list refresh, includes network failures in that recovery state, and blocks section/route navigation while saving or reconciling. Temporary-password reset, account deletion, populated role workflows, database cutover, and live hosted writes remain unverified or unimplemented. No real Auth key or user was created for this work.

Supabase references: [Auth admin access](https://supabase.com/docs/reference/python/admin-api), [administrator-created users](https://supabase.com/docs/reference/python/auth-admin-createuser).
