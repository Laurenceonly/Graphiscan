# Legacy MySQL to Supabase PostgreSQL

Latest assignment setup checkpoint (2026-10-20): 011 is user-reported applied and all ten independent hosted read-only metadata/zero-identity checks passed. No writes, credentials, grants or records changed. Updated API5002 is running (session 99903): live health 200, unauthenticated options 401 and admin /access 200. Next: user signs in with the existing fictional Auth account/current password and confirms Students/Schools sections. Empty scope can be correct; no automatic management grant or populated-write evidence is implied. Overall rough progress remains 35%. Older installation-pending notes below are historical; do not repeat SQL/password/seed setup.


Latest workspace/options slice (2026-10-20): both /access ready states now include shared school/student lists, filters, details and forms, eligible teacher/parent selectors, revision recovery and explicit same-payload student creation retry. New assignment-options read route is local; UNAPPLIED 011 adds only an existing-reader fixed-path definer read capability, no data/grants/credentials. 156 Python/11 JavaScript/494 contract/284 isolated SQL checks and both Vue builds passed. Vite pages/modules returned 200; browser inventory was empty, so visual/live authorized form checks remain unverified. Next: apply only 011 once, verify hosted function metadata/zero-identity denial, restart API5002 and user-check Students/Schools sections. No automatic privilege seed or data migration. Rough overall progress is 35%; earlier checkpoints below are historical. See graphiscan/api/WORKSPACE_DIRECTORY.md.


Latest hosted mutation checkpoint (2026-10-20): 010 is user-reported applied. All 26 hosted metadata/invalid-session checks passed. Metadata was read-only; row-locking zero-identity writer probes were explicitly rolled back, with no application writes committed or private data/key output. Updated API5002 (session 6207) passed live health 200, four unauthenticated write routes 401 and PATCH/Idempotency-Key preflight. Authorized hosted writes/retries/concurrency and resource UI remain pending. Next: eligible assignment choices and school/student screens. No repeat SQL/password/seed setup. Rough overall progress remains 34%; older installation-pending notes below are historical.


Latest directory mutation slice (2026-10-20): school/student POST/PATCH are implemented locally with scoped assignment checks, profile/record locks, optimistic revisions, private duplicate warnings and durable HMAC-bound student creation retries. Unapplied 010 reuses the existing function-only writer, initializes a private random request-digest key and adds no application records/grants or new credentials. 151 Python/494 contract/265 isolated SQL checks passed; OpenAPI has fifteen foundation operations of 33. Next: apply only 010 once, inspect hosted permissions/zero-identity denial and restart API5002. Actual hosted writes/concurrency, assignment-option queries and resource UI remain pending. Rough overall progress is 34%; older checkpoints below are historical.


Latest hosted directory checkpoint (2026-10-20): 009 is user-reported applied. All 15 independent read-only function security/grant/zero-identity checks passed; no hosted writes or private record output. Updated API5002 is running: live health 200, three directory routes 401 without bearer after stopping superseded GraphiScan Python processes. Authenticated hosted record/scope requests and record UI/writes remain separate work. Do not repeat migrations/password/seed setup. Rough overall progress remains 33%. Older installation-pending notes below are historical.


Current checkpoint (2026-10-20): migrations 001–008 are user-reported applied;
008 function security/grants were independently inspected read-only. New
**unapplied 009_directory_reads.sql** installs one bounded fixed-path definer
read function for the existing reader, with no table grants, credentials, record
imports or client policies. Local authorization SQL passed 45 new directory
checks (210 SQL total), plus 140 Python/494 contract checks. Hosted directory
installation/resource requests and record migration remain pending. See
[directory runbook](../api/DIRECTORY_ACCESS.md). Older setup notes below are history.

Actual read-only hosted preflight passed on 2026-10-20 (24 checks): verified
CA/TLS reader connection/settings, public grants/RLS, session trigger/function
metadata and zero-identity denial. The inspector works without Auth schema USAGE
via catalog OIDs; no extra hosted grants were added. No records were imported or
changed. Real user Auth bootstrap and migration/rollback remain unverified.

Latest: user reported 001-004 success and expected schema metadata. New **unapplied
005** creates a NOLOGIN reader, six SELECT policies and a restricted definer
session accessor, without reader bypass/direct Auth SELECT or managed Auth policy
changes. The invalidation trigger also becomes a fixed-path definer for restricted
future writers. Apply as the reviewed owner with Auth access, then set reader
credentials privately. The canonical query now requires 005. Passed 49 Python,
464 contract and 83 isolated SQL checks; actual hosted setup remains pending.

The optional v1 adapter now queries current access via `postgres/access_snapshot.sql`.
Unapplied `postgres/004_session_access.sql` adds a monotonic session floor and
revokes existing application session IDs on profile/security changes. It requires
the real Supabase `auth.sessions` fields `id`, `user_id`, `created_at`, `not_after`;
the invoker trigger needs Auth SELECT and revocation INSERT permissions for future
profile-write roles. All four drafts and the access query passed isolated PGlite
checks with fictional Auth tables (32 prior plus 31 access/security checks).
No hosted schema, role grants, provider sessions or real records were changed.
Hosted schema/version compatibility, concurrent Auth transactions, backup and
rollback remain to verify. See the API README for the read-only adapter's setup.

See [the proposed shared API contract](../../API_CONTRACT.md) and [artifact validation notes](../api/README.md) for wire types, ownership/onboarding, historical models and private images. `postgres/003_api_contract.sql` now extends the original identity/screening drafts with permission/school scope, expert assignment, revisions/history, consent publication, session revocations, request tracking, cleanup and model metadata. All three passed isolated in-memory PostgreSQL checks with an `auth.users` stub and fictional rows; none was applied to live MySQL or hosted Supabase. Existing MySQL cascade deletions conflict with target RESTRICT relationships; retention/deletion policy remains unresolved. No grant, consent text or real model default is seeded.

This is a migration plan, not a completed data transfer. The source is the schema-only `legacy_mysql_schema.sql` extracted from an export dated 2026-07-28. The folder `C:\Users\MY_PC\Downloads\CAPSTONE\graphiscan_db` contains raw MySQL/MariaDB `.frm` and `.ibd` files; these are not PostgreSQL imports. The XAMPP database copy has later file timestamps. Obtain a fresh logical SQL export and a secure backup before moving real rows.

| Existing MySQL table | Target |
| --- | --- |
| `users` | Supabase Auth credentials plus `user_profiles`; map integer IDs to Auth UUIDs. Do not copy password hashes into the new app as usable passwords. Create temporary credentials through the approved account-issuance flow. |
| `students` | `students` plus required `schools`; normalize grade text to integer 1, 2, or 3 and reconcile school assignment. |
| `handwriting_samples` | `handwriting_samples`; move files into a private Storage bucket and store object paths, not local Flask static paths. |
| `results` | `screening_results` with the historical binary model/version and `task_type = 'binary'`. Convert stored percentage scores to fractions in 0–1. Never infer a Low Potential class from old Normal results. Do not import obsolete AI advice. |
| `validations` | `expert_validations`; map expert IDs and retain expert-authored remarks/recommendations. |
| `reports` | `screening_reports`; reconcile one Initial report per student and label later reports Follow-up by actual assessment order. |
| `audit_logs` | `audit_logs`; map actor IDs where possible and review old action text for unnecessary personal details. |
| `password_reset_tokens` | Do not migrate. Supabase Auth handles future password resets; old reset tokens should not remain valid. |

Target definitions are in `postgres/001_identity.sql`, `postgres/002_screening.sql` and `postgres/003_api_contract.sql`. Their isolated validation is schema/constraint evidence only. The final migration still needs a secure import program, hosted service/role checks, rollback plan, server API conversion, and reconciliation of counts, relationships and unavailable historical evidence. Keep the original export and raw database files outside Git.
