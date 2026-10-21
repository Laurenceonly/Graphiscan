# Temporary test notice and versioned acceptance

Applied015 checkpoint(2026-10-20): user reported atomic bundle success; all23 agent-run restricted read-only setup checks passed, including new exact4-ID notice/hash, old notice preservation and audience function gates/ACLs. Updated hosted5002 session43462 active. Do not repeat015/old seeds/privacy checkers. Next fresh admin sign-in and explicit new notice acceptance with current password; no reset. Newroles each complete their own forced password change and notice. Actual new-version acceptance/role resource flow remains pending; metadata checks do not establish it.

2026-10-20 extension: UNAPPLIED015_workflow_fixtures.sql is the single atomic handoff for the selected fictional-role test. It adds a bounded1–16 UUID test audience to acceptance, directory/screening gates and backward-compatible bootstrap/notice reads. It then creates selected fictional fixtures and publishes [the new separate notice](fictional-workflow-notice.txt) for only the exact4 IDs. Original singleton notice text/audience/acceptance rows remain intact; only its current flag is retired. All4 accounts must explicitly accept the new version; newroles must first change temporary passwords, admin password remains unchanged. No acceptance seeded or old notice unscoped.162 v1/114 isolated SQL checks passed; no hosted application yet. See [workflow setup](FICTIONAL_WORKFLOW_SETUP.md). Apply ONLY the bundle, not its source files or prior migrations. Never rerun original privacy/forced-first-change checkers against the new state unchanged.

Passing hosted user-run checkpoint (2026-10-20): `privacy-check-passed`, all nine
checks passing, including exact notice display, explicit saved acceptance, repeat
timestamp preservation, stale-version denial, bootstrap and gate-only readiness,
and session cleanup. No credentials were saved/shared and no password changed.
Do not repeat setup/checkers just to reproduce passing evidence. This supersedes
pending-acceptance notes below; it establishes standalone fictional testing, not
client integration, resource permission or real student/guardian consent.

Latest hosted checkpoint (2026-10-20): user executed the seed twice, with an error
on the second run. Independent read-only inspection verified all eight flags:
single current canonical/hash-matching version, authorized test-publication
metadata, expected active scoped fixture, no acceptance yet and restricted
installed acceptance function. The saved state is correct; do not rerun or repair
the seed. The exact error was not supplied, but repeat refusal is intentional.
Next is the interactive checker at step 3 below; no password setup is needed.

Hosted setup checkpoint (2026-10-20): user reported successful 007 execution.
Do not rerun it. Next is the owner-run fictional notice seed, then the interactive
acceptance checker. No notice publication or acceptance has yet been reported;
no independent hosted acceptance verification occurred in this checkpoint.

The user authorized a temporary notice for fictional-account testing on
2026-10-20, with later revisions expected. This is test-use authorization, not
institutional approval for collecting real student records. The user-facing
canonical text is [test-notice-v1.txt](test-notice-v1.txt); the earlier
[review brief](../../PRIVACY_REVIEW_BRIEF.md) remains an internal input list.

## Implemented locally

- `GET /api/v1/privacy-agreement` returns only the current approved, published,
  content-hash-matching notice's version/title/content/publication time. Current
  active identity and a completed password gate are required. Missing/unpublished/
  corrupted/out-of-scope notice returns 503 `AGREEMENT_NOT_CONFIGURED`.
- `POST /api/v1/me/privacy-acceptance` accepts exactly `agreement_version` and
  `accepted: true` in a bounded JSON body. It rechecks provider session, durable
  revocation/security floor, pending credentials, account status, password gate,
  current notice/version/hash and subject scope in the database transaction.
- Migration **007** (now user-reported applied) adds optional `privacy_agreements.test_subject_id` and
  `graphiscan_accept_privacy`. The temporary fixture is bound to the existing
  fictional Auth profile. Other users see no required notice and cannot accept
  it; their normal protected access remains blocked. Non-test agreements may
  later use a null subject after real wording/approval is established.
- The existing function-only `graphiscan_password_writer` gains EXECUTE on this
  one onboarding function. It gains no direct table/Auth privileges. No extra
  role, login or password is created, and the reader stays read-only.
- Acceptance and one audit row commit atomically. Repetition preserves the
  original acceptance time and creates no duplicate audit. Profile locks order
  acceptance with security updates; a shared notice-row lock orders it with
  publication updates. The response records server time, not a client time.
- A changed/superseded version returns 409 `AGREEMENT_CHANGED`. Published text is
  immutable: revise by publishing a new version, never editing the existing
  version. Bootstrap and the normal guard immediately require that new version;
  historical acceptance remains linked to the historical text.

The snapshot uses a JSON-column projection so it still runs before 007 is
applied. Without 007, new acceptance calls fail closed; no application-table write
is attempted by a reader. Existing MySQL/Vue/older Flask paths retain their current
behavior. No UI cutover or real-data consent deployment is included here.

## One-time disposable hosted setup

1. Review and owner-run `db/postgres/007_privacy_acceptance.sql` once in the same
   disposable project after 001-006. It publishes no notice and accepts nothing.
2. Then review and owner-run `db/postgres/seed_test_agreement.sql` once. It resolves
   only `graphiscan.test@example.invalid` with the expected synthetic active admin
   profile and completed password change, refuses an existing current notice or
   fixture version, publishes the exact canonical `graphiscan-test-v1` text with
   its hash and test subject, and audits publication. Approval metadata here
   records the authorized test fixture, not legal/institutional approval. It does
   not create an acceptance or alter credentials, grants or student data.
3. In a local terminal from the repository root, run:

   ```powershell
   .\.venv\Scripts\python.exe .\graphiscan\tools\check_v1_privacy.py
   ```

   Enter the fictional Auth account's **current newly saved password** from the
   passing password check. This command does not change that password. It shows
   the exact notice and only submits acceptance if the user explicitly types
   `ACCEPT TEST NOTICE`. Declining records no acceptance. The checker verifies
   saved acceptance, stable timestamp on repetition, stale-version denial,
   bootstrap readiness and a gate-only probe, then cleans up its provider session.
   The probe does not grant any resource permission or assignment. Only share the
   JSON status report; never passwords/tokens. Passwords are hidden, CLI/piped
   credentials are refused, and the checker saves no credentials.

No 007/fixture publication or hosted acceptance has been executed by the agent.
Do not repeat prior migration/password setup. The seeded test version must be
reviewed/replaced before any real-user deployment; it permits fictional testing
only and specifies that real student information must not be submitted.

## Revision and verification boundaries

A later approved notice needs a new version/title/content/hash and approval/
publication record. Change the single current version in an owner-reviewed
transaction. Old acceptance is not migrated or relabeled. Do not reuse the
temporary notice's acceptance as real participation/guardian permission.

Python tests mock HTTP/storage. PGlite runs actual functions, triggers, permissions,
seed and snapshot SQL with fictional Auth records; it does not prove simultaneous
hosted transactions, provider concurrency or deployed client behavior. Hosted
publication/acceptance and concurrent publication/security mutation remain
unverified until exercised separately.

Technical sources reviewed 2026-10-20:
[PostgreSQL row locks](https://www.postgresql.org/docs/17/explicit-locking.html),
[READ COMMITTED behavior](https://www.postgresql.org/docs/16/transaction-iso.html).
The distinction between a notice and consent is also described by the
[National Privacy Commission](https://privacy.gov.ph/the-right-to-be-informed/).
These sources do not approve this temporary text or establish legal compliance.
