# Hosted screening read integration

Migration 012_screening_reads.sql is **user-reported applied and independently checked** (2026-10-20). All 22 hosted read-only metadata/privilege/nonexistent-identity checks passed. Updated API5002 session54308 returned health200 and 401/no-store on all four unauthenticated reads. Do not reapply it or earlier migrations. It grants one fixed-search-path read function to the existing reader, without accounts, application records, model defaults, new credentials or table privileges. Authenticated populated reads remain unverified.

The composed v1 backend now implements:

- GET /api/v1/screenings — bounded filters and signed keyset pagination.
- GET /api/v1/screenings/{result_id} — current-scope detail.
- GET /api/v1/students/{student_id}/history — newest/oldest keysets, release filtering before pagination.
- GET /api/v1/reports/{report_id} — authorized report JSON.

The database repeats current provider-session, durable revocation, account, password and versioned-privacy gates in the same statement as record scope. Teachers use current student assignment; parents require their current child link and a current Validated review; experts require the individual result's current assignment. Admin/researcher reads require global or school-scoped assignments.manage. School membership or schools.manage alone grants no screening records. Missing/inaccessible details return the same 404. Linked students can have empty history; foreign students cannot be enumerated through history. Parents see no unreleased counts or records.

Stored reports retain Initial/Follow-up labels. Hosted scores are fractions; React converts them to display percentages separately from legacy percent values. Historical model identity comes from the result snapshot, never a mutable live registry name. Unverified historical identity remains null. Historical model projection is not a selectable-model catalogue. Private storage paths, obsolete generated prose and legacy Auth identifiers are absent. This slice does not implement image access, model selection, uploads, review writes, account issuance or data import.

## React connection

The converted app has an explicit hosted mode in the same App entry point and reuses the shared hosted client:

    $env:EXPO_PUBLIC_API_MODE='hosted'
    $env:EXPO_PUBLIC_HOSTED_API_ORIGIN='http://127.0.0.1:5002'
    npm.cmd run web

Run those commands from graphiscan/mobile-app with the updated v1 API running; migration 012 is already applied. Use a suitable issued teacher/expert/parent account. The existing Synthetic Test Admin is an admin account and is deliberately rejected by the user app; use its admin workspace for that role. Do not reuse legacy MySQL passwords or map numeric IDs to Auth UUIDs. Hosted and legacy modes have separate API contracts and session closures. Legacy remains the default while hosted write parity is incomplete.

Android emulators need http://10.0.2.2:5002; physical phones need a reachable LAN development origin or deployed HTTPS API. These are public configuration values, never secret keys. Restart Expo when changing public variables. The current temporary notice is scoped to the single fictional admin: real issued-role onboarding remains unavailable until an appropriately reviewed notice is published. This code does not bypass that gate or expand the test notice's audience.

Hosted mode connects sign-in, mandatory password change, exact-version notice acceptance, students, results, history, report detail and sign-out. Camera uploads, review submission, image sharing and student creation continue to exist in the legacy conversion mode, but are not silently routed to MySQL from a hosted session. Their hosted endpoints are subsequent work. No release/deployment or complete data migration is claimed.

## Verification

The new PostgreSQL function is exercised with fictional PGlite fixtures, including changed assignments, withdrawn validation, provider-session removal and protected role privileges. HTTP/service tests use stubs. Shared-client tests cover logout races, refresh and absence of write replay. React TypeScript and web/Android JS exports verify compilation, not native/device behavior. All 22 hosted metadata/privilege/nonexistent-identity checks passed after application of 012; authenticated populated role/read checks remain pending.
