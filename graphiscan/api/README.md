# Shared API artifacts and runtime foundation

Current reconciliation (2026-10-22): OpenAPI declares34 foundation operations
and2 proposed operations. Migrations through019 are installed; admin/API are
published and hosted admin login/dashboard is user-confirmed. Public inference
is disabled on the admin-only Render service. Earlier unapplied012-014 and
operation-count checkpoints below are historical; do not repeat setup. Full
hosted role/write/Storage flows remain open. See `../../CURRENT_REQUIREMENTS.md`.

Latest local implementation: 26 of33 operations now have foundation handlers, including upload/review/assignment, models, request recovery and private images. **The atomic 013+014 bundle is prepared but unapplied.** Apply only 013_014_screening_writes.sql once, then preflight/restart. React hosted actions are connected; private Storage, pinned supported model/reviewed registry evidence, user-role setup, real hosted/device checks and deployment remain pending. See [screening writes](SCREENING_WRITES.md); do not treat these local checks as live screening evidence.

Latest verification (2026-10-20): 012 is user-reported applied and all 22 independent hosted read-only metadata/privilege/nonexistent-identity checks passed. Updated API5002 session54308 returns health200 and all four unauthenticated screening read routes401/no-store. No application writes or repeated setup; authenticated populated/device/write checks remain pending. Earlier unapplied/restart notes below are superseded.

Latest (2026-10-20): twenty of 33 operations now have local foundation handlers, including protected screening list/detail, student history and report JSON. **012_screening_reads.sql is prepared, unapplied**; earlier migrations remain applied as recorded. React explicit hosted mode connects Auth/onboarding and these reads; legacy stays default until write parity. See [screening read integration](SCREENING_READS.md). Isolated SQL/HTTP/client tests and exports pass, without authenticated hosted/device/deployment evidence. This checkpoint supersedes older counts/next steps below.

Latest assignment setup checkpoint (2026-10-20): 011 is user-reported applied and all ten independent hosted read-only metadata/zero-identity checks passed. No writes, credentials, grants or records changed. Updated API5002 is running (session 99903): live health 200, unauthenticated options 401 and admin /access 200. Next: user signs in with the existing fictional Auth account/current password and confirms Students/Schools sections. Empty scope can be correct; no automatic management grant or populated-write evidence is implied. Overall rough progress remains 35%. Older installation-pending notes below are historical; do not repeat SQL/password/seed setup.


Workspace update (2026-10-20): assignment choices and shared directory screens are implemented locally; 011 is unapplied. OpenAPI now has sixteen foundation operations of 33. Current evidence: 156 Python/11 JS/494 contract/284 SQL checks and both builds passed. See [workspace setup](WORKSPACE_DIRECTORY.md). Older counts/setup checkpoints below are historical.


These describe a **draft target with a small runtime foundation**. `api_v1.py`
registers `/api/v1/health`, `/me`, `/me/password`, `/privacy-agreement`,
`/me/privacy-acceptance`, session login/refresh/logout, `/schools`, `/students`
and `/students/{student_id}`, with school/student POST/PATCH through `app.py`.
OpenAPI marks those fifteen
operations `foundation`; all other operations remain `proposed`. Optional Auth
and PostgreSQL access adapters exist in `v1_backend.py`; a disposable hosted
read-only connection/grant preflight passed. User reported browser sign-in,
account readiness and sign-out working. Directory migration 009 is verified;
mutation migration 010 has passed hosted metadata/invalid-session checks. Actual authorized hosted resource reads/writes,
storage integration and record-client migration remain pending.
Default protected access fails closed: missing bearer syntax returns 401; a
bearer with the unconfigured backend returns 503. Health is process liveness only.

- [Human-readable contract](../../API_CONTRACT.md): policies, data semantics,
  current-to-target differences and unresolved inputs.
- [openapi.json](openapi.json): canonical machine-readable OpenAPI 3.0.3 draft,
  33 operations, strict mutation bodies, typed responses and bearer security.
- [access-cases.json](access-cases.json): 19 proposed integration scenarios.
  They are checked for valid operation/status references, not executed against
  real resource authorization. Separate synthetic tests exercise the runtime guard.
- [003_api_contract.sql](../db/postgres/003_api_contract.sql): unapplied schema
  extension after the two existing drafts. No policy grants or real data seeded.
- [check_api_contract.cjs](../tools/check_api_contract.cjs): offline structural,
  payload, SQL constraint/trigger and RLS verification.

Edit the canonical JSON and prose together. Paths are relative to `/api/v1`;
`x-roles`, `x-permission`, `x-record-scope` and `x-gates` are declarations that
server middleware must implement. Generating a client does not implement them.
The spec has no DELETE operations while retention/permanent deletion is unresolved.

## Runtime foundation

Mutation slice (2026-10-20): [DIRECTORY_WRITES.md](DIRECTORY_WRITES.md) documents
four school/student POST/PATCH operations and unapplied 010. 151 Python/494
contract/265 isolated SQL checks passed. Function-only writes recheck current
authorization/eligible links, revisions, idempotent student creation and audit.
No resource frontend or hosted write verification is implied.

Read-only directory slice (2026-10-20): [DIRECTORY_ACCESS.md](DIRECTORY_ACCESS.md)
documents three implemented school/student GET operations and unapplied 009.
140 Python, 494 contract and 210 isolated SQL checks passed. No new frontend,
record writes, privilege seeding or hosted resource verification is implied.

Shared sessions/client slice (2026-10-20): [SESSION_INTEGRATION.md](SESSION_INTEGRATION.md)
documents login/refresh/logout, unapplied 008 and both apps' actual `/access`
onboarding flow. Contract now has 33 operations/eight foundation operations.
129 Python/seven JS-client/494 contract/165 isolated SQL checks and both builds
passed. Updated local onboarding API uses port5002; legacy records remain on
their original API. Actual hosted browser/session verification awaits 008;
this does not complete resource/client cutover.

Latest privacy evidence (2026-10-20): user supplied all nine passing hosted
notice/acceptance checks, including explicit acceptance, repeat/stale-version
behavior, bootstrap/gate readiness and cleanup. Fictional test participation
only; no real-use consent, resource authority or client integration is implied.
See [privacy runbook](PRIVACY_ACCEPTANCE.md). Do not repeat completed setup.

Temporary notice/acceptance slice (2026-10-20): user authorized fictional-account
test use, revisable later. [PRIVACY_ACCEPTANCE.md](PRIVACY_ACCEPTANCE.md) documents
canonical text, subject-scoped read/atomic acceptance, unapplied 007, optional
owner seed and explicit hidden-prompt checker. All 118 Python, 466 contract and
151 isolated SQL checks passed. Hosted 007/publication/acceptance remain pending;
no new DB role/password is required. Real-use privacy approval remains unresolved.
Older pending statements below are historical.

Latest user-run hosted password checkpoint (2026-10-20): all 12 checks passed,
including actual endpoint/old-password/session denial/fresh bootstrap/privacy
gate/cleanup. No credentials were shared/saved. Application writes may have
occurred, and the fixture first-change flag is now cleared; do not rerun its
forced-state checker unchanged. Reader/writer preflights passed 24/23 actual
checks. Latest local evidence: 103 Python, 465 contract, 123 isolated SQL. Next is
approved privacy wording/version and agreement acceptance/client onboarding.
Hosted refresh, concurrent/distributed failure recovery, generic login/logout
and client integration remain separate work. Earlier pending statements below
describe their historical checkpoints; see [PASSWORD_CHANGE.md](PASSWORD_CHANGE.md).

Password slice (2026-10-20): [PASSWORD_CHANGE.md](PASSWORD_CHANGE.md) documents
the local endpoint, separate writer, unapplied migration 006 and fictional-account
recovery. All 84 Python, 465 contract and 119 isolated SQL checks passed. Hosted
password/writer/recovery/concurrency and client integration remain unverified.
Without the separate private writer setting the endpoint returns 503. This
supersedes older statements below that password routes are unimplemented.

After the fictional Auth user/profile exists, `tools/check_v1_auth.py` provides
a manual hidden-prompt login/bootstrap/gate/local-sign-out check. It never saves
or prints credentials and refuses CLI/piped passwords. See the hosted runbook
for the command and scope. On 2026-10-20 the user supplied `auth-check-passed`
with all 11 checks passing, including real sign-in, verified bootstrap, password
gate, local cleanup and revoked-session denial. No application writes or saved
credentials were reported. This is user-run hosted evidence; production session/
password endpoints and client integration remain open. All 61 Python tests
passed using synthetic HTTP/DB fixtures.

Run from `graphiscan/` with the existing virtual environment:

```powershell
& '../.venv/Scripts/python.exe' -m unittest discover -s tests -v
```

`tests/test_api_v1.py` imports only the standalone module and uses fictional
identity/access adapters. It exercises current account/session denial, password
then privacy gates, bootstrap projection, scoped grants, role ceilings and
record callbacks. Its test-only routes are never registered in the application.
Existing regression tests additionally import `app.py` with local configuration.
The access-case JSON still describes future real-resource integration tests.

Server composition may pass an `AccessBackend` to `install_api_v1`. Its
`authenticate` method must verify provider tokens and durable session validity;
`load_access` must read coherent, current profile/grant/membership/agreement state
and enforce credential/security-version invalidation. Unavailability raises
`BackendUnavailable`, denial raises `InvalidSession`. No environment setting
enables a test identity. Missing profile/unavailable account gets a minimal 403.
The optional Supabase/PostgreSQL adapter is described below; hosted verification
is still required before deployment.

Use `require_access` for feature gates. Real record routes must supply a current
`record_scope` callback and scope-filter list queries before pagination/counts.
Membership or `/me.permissions` alone never authorizes a record. Synthetic
callbacks demonstrate the contract; they do not implement SQL record ownership.
The guard does not implement logout, password change or agreement acceptance.
All foundation responses carry generated request IDs and `Cache-Control: no-store`.

## Optional trusted adapter (not deployed)

Actual read-only hosted preflight passed on 2026-10-20 with 24 checks; optional
user-token bootstrap was not run. Downloaded CA verification and reader login/
grants/RLS/metadata/zero-identity checks succeeded. Existing clients still use
the legacy API; actual Auth sign-in and session bootstrap remain to verify.

Use [HOSTED_PREFLIGHT.md](HOSTED_PREFLIGHT.md) for disposable-project preparation,
the read-only checker commands and coverage limits. `check_v1_hosted.py` defaults
to offline configuration checks and requires `--connect` for network access.
Its JSON report contains no credential/profile values. The local run found the
four required v1 settings absent and attempted no network connection or DB write.

Install `requirements-v1.txt` alongside the existing runtime requirements. Copy
only the variable names from `.env.example` into private server configuration:

- `GRAPHISCAN_V1_BACKEND=supabase-postgres` explicitly opts in.
- `GRAPHISCAN_V1_SUPABASE_URL` is the trusted HTTPS project origin, without a path.
- `GRAPHISCAN_V1_SUPABASE_PUBLISHABLE_KEY` is a publishable key; secret/service-role
  keys and legacy anon JWT keys are not accepted by this adapter.
- `GRAPHISCAN_V1_DATABASE_URL` is a private PostgreSQL DSN for the reviewed target
  project. Never put the DSN in a client build or tracked file.

No network connection is made during startup. Missing/invalid configuration or a
missing optional driver keeps v1 unavailable. Existing MySQL routes remain separate.
The connection forces `sslmode=verify-full`, UTC, a five-second statement timeout,
and read-only transactions. Supply the trusted CA using libpq's certificate
configuration when required; insecure TLS in a DSN does not override verification.

The adapter calls Supabase `/auth/v1/user` for the exact bearer on every request,
without redirects, then binds signed subject/session claims to the returned user.
It also checks issuer, audience and token times. There is no local signature
verifier or trust in client role/metadata. See [Supabase getUser](https://supabase.com/docs/reference/javascript/auth-getuser).
A single parameterized query in `access_snapshot.sql` checks the owned provider
session, `not_after`, durable revocations, pending credential updates and session
security floor while reading current profile, grants, memberships and agreement.
Current agreement publication must be approved, not future-dated, and its content
hash must match. The adapter supplies no fallback user, grant or agreement.

Apply reviewed 001-**005** only to a disposable Supabase project first.
004 invalidates existing session IDs on profile/security changes and maintains a
monotonic native timestamp floor, including changes from 003's grant/membership
triggers. A fresh same-tick session is permitted while an existing revoked ID is
denied. The trigger writes application revocations, never provider sessions.
Do not compare rounded JWT `iat` to a fractional password-change timestamp.
Provider session lookup follows [Supabase's session guidance](https://supabase.com/docs/guides/auth/sessions).

005 creates a NOLOGIN server reader with SELECT on six public snapshot tables
and private role-specific policies, without ownership, RLS bypass or direct Auth
SELECT. A fixed-search-path SECURITY DEFINER function returns only the requested
subject/session pair's ID/times. Client/API roles cannot execute it. The existing
session invalidation trigger also becomes a definer so future restricted profile
writers need no direct Auth grants. Apply as the reviewed schema owner with Auth
SELECT/RLS access. Reader password/LOGIN setup is separate; no credentials are in
the script. The user reported successful hosted 005 execution; private reader
LOGIN/password and connected checks remain pending. The read-only adapter cannot
apply migrations or perform onboarding/account writes.

Tests mock Auth HTTP and Python driver connections; SQL runs separately against
fictional Auth tables in PGlite. They do not establish real JWT/provider response
behavior, hosted TLS/grants/schema compatibility, refresh/sign-out integration,
concurrent Auth transactions, or project-specific session expiry/MFA policies.

## Reproduce validation

From the repository root, install the validation-only packages into the ignored
workspace folder. This leaves Flask and frontend runtime dependencies unchanged:

```powershell
npm.cmd install --prefix .local-tools/api-validation --no-save --package-lock=false @apidevtools/swagger-parser@13.1.0 @electric-sql/pglite@0.5.10 ajv@8.20.0 ajv-formats@3.0.1
node graphiscan/tools/check_api_contract.cjs
```

Once installed, the check itself needs no network, credentials, XAMPP, Docker or
Supabase project. Swagger Parser checks OpenAPI structure/references; Ajv checks
payload acceptance/rejection. PGlite creates an in-memory PostgreSQL instance,
stubs only the queried fields of `auth.users`/`auth.sessions`, applies 001-005,
uses fictional records, exercises the canonical access query,
constraints/triggers and a non-owner RLS role, then closes it. It never imports
`config.py` or connects to a live database. [PGlite engine documentation](https://pglite.dev/docs/).

The SQL checks cover class/score boundaries, report uniqueness, conditional stale
updates, scope revision changes, reviewer attribution and append-only history,
immutable model/result/report identity, agreement approval/current-version
constraints, request-key uniqueness/completion and default-deny direct client
access. They do **not** verify Supabase Auth/Storage service grants, JWT checking,
the live Flask authorization layer, simultaneous multi-connection uploads, data
migration, cleanup workers, hosted performance or rollback/cutover.

## Schema alignment notes

| Contract concept | Draft storage / remaining handler responsibility |
| --- | --- |
| Permission/school scope | `user_permission_grants`, `school_memberships`, `assignment_eligibilities`; handlers enforce current role/status, ceilings, school scope AND record ownership |
| Account revisions | `user_profiles.revision` and scope-change triggers; account writes still need `WHERE revision = expected_revision` and transactional grant replacement |
| Consent | `privacy_agreements`, acceptance FK and one-current index; handlers lock/check the current approved version, compute/check content hash and enforce gate ordering |
| Session denial | 004 session floor and revocation trigger; optional adapter checks provider session/current security state. Hosted integration, sign-out and credential-write orchestration remain open |
| Model evidence | `model_evaluations` plus registry provenance, class labels, preprocessing and decision rule; publication/default selection needs evaluated artifacts and server checks |
| Screening scores | DB `class_probabilities` maps to API `class_scores`; DB `confidence_score` maps to `predicted_class_score`, not maximum/clinical probability |
| Historical unknowns | `legacy_unverified` defaults; unknown internal legacy identity placeholders map to nullable public metadata, never selectable models |
| Expert assignment | `screening_expert_assignments` separate from actual reviewer; changes advance result/review revisions; role/eligibility checks remain in Flask |
| Review history | `expert_review_history` append-only trigger; current review remains in `expert_validations`; handlers check assignments/revisions and audit in the same transaction |
| Upload recovery | `api_requests` unique actor/operation/key, digest and state; handlers reserve keys, pin inference, lock student completion and reauthorize replays |
| Private objects | `handwriting_samples.storage_path`, cleanup jobs; private Storage setup, immutable object writes and authorized image proxy remain unimplemented |
| Report context | `school_context` snapshot; handler fills verified native school/grade context, returns explicit null for unavailable history, and rechecks current parent release |
| Audit | Resource/request columns added to existing audit table; native writes must fill them atomically, historical missing fields remain null |

003 defaults provenance to `legacy_unverified` so unknown records cannot silently
become verified/selectable. New v1 handlers must explicitly write verified
metadata and complete snapshots. It drops the obsolete target `analysis_summary`
column; it does not erase anything from the current MySQL application.

The drafts are intended for a fresh test schema. If a previous target schema has
records, reconcile existing consents/models/scores before applying 003; new
constraints may deliberately reject incomplete existing rows. Do not apply by
glob or run against production merely because local validation passed. No client
RLS policies are installed; test actual server-role privileges and service
configuration in a disposable Supabase project before migration.
