# Disposable hosted preflight

Current verified result (2026-10-20): actual `--connect` returned
`preflight-passed`, with 24 checks passed and optional user-session bootstrap
`not-run`. The downloaded CA is configured privately with verify-full. Reader
login/settings, six public-table SELECT-only grants/RLS, session trigger/function
metadata and zero-identity denial were checked without DB writes or profile
output. The Auth privilege inspector uses catalog OIDs and works without Auth
schema USAGE; no extra grants are needed. All 49 Python, 464 contract and 84
isolated SQL checks passed. Real Auth sign-in/session bootstrap remains next.

Preparation history: configuration was absent on 2026-10-19. The user then
reported successful 001-005 setup, matching schema metadata and a private reader
password. The first connected attempt lacked a root CA; installing/configuring
the user-downloaded CA and fixing metadata introspection produced the verified
result above. No migrations or password resets need repeating. Existing MySQL/
XAMPP services and clients remain active.

## Prepare a target

Use a separate Supabase project containing fictional records only. Create it in
the [Supabase Dashboard](https://supabase.com/dashboard/projects). Obtain its
project origin and publishable key from the Connect/API Keys screens described
in [Supabase's key documentation](https://supabase.com/docs/guides/getting-started/api-keys).
Keep DB passwords and access tokens in private local configuration.

Review and apply the canonical migration files in order using the target's
authorized schema-owner workflow:

1. `db/postgres/001_identity.sql`
2. `db/postgres/002_screening.sql`
3. `db/postgres/003_api_contract.sql`
4. `db/postgres/004_session_access.sql`
5. `db/postgres/005_api_reader.sql`

These scripts are not idempotent. Do not rerun them over existing schema objects
or point them at the current MySQL database. The preflight never applies them.
It also never creates Auth users, grants roles, seeds profiles/agreements, or
changes existing records. Schema-owner work and credential-write role setup are
separate from the read-only runtime connection.

005 creates `graphiscan_api_reader` with NOLOGIN, no password, no RLS bypass or
administrative privileges. It grants schema usage and SELECT only on:

- `public.user_profiles`
- `public.app_session_revocations`
- `public.privacy_agreements`
- `public.privacy_agreement_acceptances`
- `public.user_permission_grants`
- `public.school_memberships`

005 adds SELECT policies targeting only this private server role; RLS remains
enabled. Supabase protects `auth.sessions` with RLS too. The reader has no direct
Auth SELECT; instead it may execute a narrow SECURITY DEFINER function returning
only a requested subject/session pair's ID/times. Its search path is fixed to
`pg_catalog`, and client/API roles cannot execute it. Apply as the reviewed schema
owner with Auth SELECT/RLS access. No managed Auth policies or rows are changed.
005 also makes the existing invalidation trigger a definer so future restricted
profile writers can revoke existing session IDs without direct Auth privileges.
Login/password setup is a separate private step after 005 succeeds. Generate and
save a new strong password with a password manager. In a private SQL Editor query,
replace the placeholder below before executing (do not save a filled query in this
repository or send it in chat). For straightforward SQL entry, generate 24 or more
random characters using letters, numbers, `-` and `_`:

```sql
ALTER ROLE graphiscan_api_reader
WITH LOGIN PASSWORD 'REPLACE_WITH_YOUR_NEW_PASSWORD';
```

This enables only the already-restricted reader login. Save its password privately
for the local DSN. See [PostgreSQL ALTER ROLE](https://www.postgresql.org/docs/current/sql-alterrole.html).

Do not grant this reader to client/API roles or give it ownership, mutation, RLS
bypass or administrative privileges. The preflight inspects access; it never
applies schema, provisions roles or performs credential writes.

Get connection settings and the trusted certificate from the target dashboard.
Use the reader's credentials in the DSN. Follow [Supabase's connection/TLS
instructions](https://supabase.com/docs/guides/database/connecting-to-postgres);
this adapter forces `sslmode=verify-full`. A required CA can be supplied with
libpq's `sslrootcert`/`PGSSLROOTCERT` configuration. Never disable verification
to make a failed connection pass.

## Configure privately

In the existing private `graphiscan/.env`, add the v1 variable names from
`.env.example`, preserving current MySQL/password settings:

| Variable | Required value |
| --- | --- |
| `GRAPHISCAN_V1_BACKEND` | `supabase-postgres` |
| `GRAPHISCAN_V1_SUPABASE_URL` | Trusted HTTPS project origin, without `/auth/v1` |
| `GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY` | Target project's `sb_publishable_…` key |
| `GRAPHISCAN_V1_DATABASE_URL` | Private reader connection string for that target |
| `GRAPHISCAN_V1_TEST_ACCESS_TOKEN` | Optional short-lived access token for a fictional test user |

The optional test identity must already have a trusted active GraphiScan profile.
The preflight allows `/me` to report pending password/privacy onboarding, because
that is the bootstrap contract. It does not change passwords or accept privacy
text. Without the optional token, Auth and session-bootstrap checking is explicitly
reported `not-run`. Do not add an actual student's token or copy returned records
into reports. Existing process-local login tokens are not v1 test tokens.

## Run

From the repository root, after installing the existing runtime and optional
`graphiscan/requirements-v1.txt` dependencies:

```powershell
# Local configuration/driver parsing only; no network call.
& '.\.venv\Scripts\python.exe' graphiscan/tools/check_v1_hosted.py

# Explicit read-only connection to the configured target.
& '.\.venv\Scripts\python.exe' graphiscan/tools/check_v1_hosted.py --connect
```

JSON output contains setting/check names and statuses, never setting values,
DSNs, hostnames, account IDs, names, tokens or adapter exception text. Missing
configuration returns `blocked`; valid offline setup returns `ready-to-connect`.
A completed read-only pass returns `preflight-passed`; failed checks stop early.
Python exit codes are 0 for ready/pass, 2 for blocked, and 1 for failure.

The connected check verifies read-only/UTC/timeout settings, the reader's table
privileges and RLS flags, the enabled row-level BEFORE UPDATE session trigger,
and the canonical snapshot query with a nonexistent zero identity. If supplied,
the test token goes through the real adapter and a standalone Flask `/me` request;
the response is reduced to status/projection/no-store checks and is not printed.
The runner does not start the legacy Flask app or load its predictor/MySQL config.

## Evidence and remaining work

### Private interactive Auth lifecycle check

User reported the fictional profile seed succeeded on 2026-10-20. The next check
needs the Auth-account password entered locally, without putting it in chat,
command history, `.env` or a report. Open an interactive Windows PowerShell window
and run this command (works from any directory):

```powershell
& 'C:\Users\MY_PC\Downloads\CAPSTONE\capstone\.venv\Scripts\python.exe' 'C:\Users\MY_PC\Downloads\CAPSTONE\capstone\graphiscan\tools\check_v1_auth.py'
```

At the hidden prompt, enter the password for `graphiscan.test@example.invalid`,
**not** the database-reader password. No characters are echoed. The checker
rejects piped input and command-line arguments rather than falling back to echo.
It signs in, verifies the provider subject and GraphiScan bootstrap/forced-change
gate, signs out only that new session, checks the durable session denial and
confirms the original token no longer reaches `/me`. It attempts session cleanup
even after later check failures; a cleanup failure is reported as a failed check.
Do not automatically retry failed logins.

Output contains check statuses and, on sign-in denial, only HTTP status and a
fixed allowlisted reason. It contains no password/token/identity/profile or raw
provider error text. `auth-check-passed` is the expected result for this fresh
fixture. Auth login/logout creates/removes its provider test session; application
tables are read-only. No session credentials are persisted. The protected probe
exists only in a standalone Flask test app, not in the real application. This
does not implement target login/logout/password-write endpoints or prove the
current Vue apps can use Supabase login. Twelve offline cases passed (61 Python
tests total). After an initial rejected attempt, the user supplied a successful
hosted retry on 2026-10-20: `auth-check-passed`, all 11 checks passing, provider
session created, no application database writes and no saved credentials.
This is user-run evidence of sign-in/bootstrap/password gating/local logout and
revoked-session denial, not production endpoint or client integration evidence.
Next implementation is first-login password change/session invalidation with
scoped writes and failure-path checks; privacy acceptance needs approved wording.

### Optional fictional profile for Auth testing

After the manually created, auto-confirmed Auth account
`graphiscan.test@example.invalid` exists, run
`db/postgres/seed_test_profile.sql` once as the reviewed owner in the disposable
test project. User reported creating that Auth account on 2026-10-20; actual
sign-in has not run. Use a fresh private account password, separate from the DB
reader's, and keep it out of chat/tracked files.

The seed looks up the Auth UUID itself, creates a synthetic initial-admin profile
and test audit row atomically, requires password change, and grants no action
permissions or privacy acceptance. It refuses missing/ambiguous Auth users and
existing profiles. It is optional test fixture setup, not an app account-issuance
flow, and it must not be run against a project with real records. Seven isolated
seed checks passed (latest SQL total 91); user execution remains pending.

Local verification passed 49 Python tests, 464 contract checks, 32 prior SQL checks,
40 access/security checks and 11 catalog preflight checks. Python hosted behavior
uses fictional driver/HTTP fixtures; the exact catalog/access SQL executes in
isolated PGlite with fictional Auth tables and a reader role.

An offline or read-only preflight pass is not full hosted integration. Actual
provider refresh/sign-out, signed-token rejection, role/ownership mutations,
concurrent Auth/profile transactions, temporary-password/privacy writes,
private storage, migration and rollback need separate integration evidence.
