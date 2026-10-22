# GraphiScan shared API contract

Current declaration review (2026-10-22): OpenAPI contains36 operations,34 marked
foundation and2 proposed (`/summary`, `/demo-screenings`). These are source
declarations, not36 verified hosted workflows. Schema through019 is installed;
admin/API publication and user-reported login/dashboard are recorded in the
latest CHANGELOG. Guest demo is excluded from current core work. Use
[CURRENT_REQUIREMENTS.md](CURRENT_REQUIREMENTS.md) for remaining integration
and release gates; old operation counts/setup statuses below are historical.

Latest assignment setup checkpoint (2026-10-20): 011 is user-reported applied and all ten independent hosted read-only metadata/zero-identity checks passed. No writes, credentials, grants or records changed. Updated API5002 is running (session 99903): live health 200, unauthenticated options 401 and admin /access 200. Next: user signs in with the existing fictional Auth account/current password and confirms Students/Schools sections. Empty scope can be correct; no automatic management grant or populated-write evidence is implied. Overall rough progress remains 35%. Older installation-pending notes below are historical; do not repeat SQL/password/seed setup.


Workspace update (2026-10-20): assignment choices and shared directory screens are implemented locally; 011 is unapplied. OpenAPI now has sixteen foundation operations of 33. Current evidence: 156 Python/11 JS/494 contract/284 SQL checks and both builds passed. See [workspace setup](graphiscan/api/WORKSPACE_DIRECTORY.md). Older counts/setup checkpoints below are historical.


Runtime setup update (2026-10-20): the optional bootstrap adapter requires
`005_api_reader.sql`. It supplies a restricted NOLOGIN server role, six SELECT
policies and a narrow definer session lookup for Supabase's RLS-protected Auth
table; clients receive no new table or function access. The user reported 001-005
execution, and actual verify-full reader/schema preflight passed 24 checks.
Real Auth token/bootstrap and target write/resource flows remain pending.

Status: **target v1 baseline with implemented sessions, onboarding and directory reads/mutations, updated 2026-10-20**. Fifteen of 33 operations have runtime handlers: health/bootstrap, session login/refresh/logout, password/notice operations, school/student GETs and POST/PATCH mutations. Missing trusted configuration fails closed. Hosted Auth/password/privacy and user-reported `/access` sign-in/readiness/sign-out are recorded in runbooks. Directory migration 009 is verified; 010 metadata and denial probes passed; authorized hosted resource verification remains pending. Existing record clients still use `/api/admin/*`, `/api/user/*`, MySQL and the binary predictor. No record/storage migration or production cutover occurred.

The [OpenAPI 3.0.3 draft](graphiscan/api/openapi.json), [proposed integration cases](graphiscan/api/access-cases.json), and [validation/schema notes](graphiscan/api/README.md) accompany this document. Optional trusted Auth/PostgreSQL adapters require explicit server configuration. 003-005 extend the earlier drafts and passed isolated PostgreSQL tests; the user reported their execution in a disposable hosted project. Actual TLS/reader-grant preflight passed. Provider Auth/concurrency and credential/session writes remain unverified or unimplemented as applicable; the working MySQL application has not been migrated.

Sources of project requirements: [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md), [PROJECT_PLAN.md](PROJECT_PLAN.md), [defense minutes](GraphiScan_Defense_Minutes.md). Source comparison: `graphiscan/app.py`, `graphiscan/predict.py`, both client API helpers, and `graphiscan/db/postgres/001_identity.sql` / `002_screening.sql`.

## 1. Common wire rules

- Proposed base path: `/api/v1`. Both clients use the same resource routes; Flask filters and authorizes using the authenticated actor. Clients cannot select their effective role or scope through request fields.
- HTTPS for hosted services. Protected requests use `Authorization: Bearer <Supabase access token>`. Do not place credentials or tokens in URLs. Return `Cache-Control: no-store` on protected JSON, reports, images, and credential operations.
- JSON uses `snake_case`. User IDs are UUID strings. Database bigint resource IDs are **decimal strings** in JSON and paths so JavaScript cannot round them. `grade_level` is integer 1, 2, or 3. Flags are JSON booleans. Dates/times use UTC RFC 3339 strings; clients format local dates. Missing known values are `null`, never fabricated zeroes.
- Scores are fractions in `[0,1]`, not percentages. Multiply by 100 only for display. Display labels retain `Normal`, `High Potential`, and, only for a validated three-class task, `Low Potential`. Review states retain `Pending`, `Validated`, `Flagged`; report types retain `Initial Screening`, `Follow-up Screening`.
- Reject unknown mutation fields and invalid enum/type values with 422. Fields owned by the server include actor IDs, timestamps, report type, prediction/review provenance, permissions, and score values. Never accept those as client-authored screening output.
- Single-resource success: `{"data": {...}, "request_id": "..."}`. List success: `{"data": [], "page": {"next_cursor": null}, "request_id": "..."}`. Creation returns 201 and a `Location` resource path; successful reads/updates return 200. Lists accept `limit` (default 25, maximum 100), opaque `cursor`, and supported filters only. Stable ordering uses timestamp plus ID; cursors bind to actor scope/filter/order. Scope filtering happens before pagination and aggregate counts.
- Default screening/history ordering is `date_generated DESC, result_id DESC`; history accepts `order=oldest` for ascending order. Account/student/school lists use stable name-plus-ID ordering. An invalid cursor/filter produces 422. Use parameterized database queries and allowlisted sorting.
- Audit successful writes with actor, action, resource ID, time, and request ID in the database transaction. Do not log passwords, bearer tokens, raw uploaded images, or request bodies containing private records. Review history is protected application data, not text copied into broadly readable log messages.

Error shape:

```json
{
  "error": {
    "code": "PRIVACY_ACCEPTANCE_REQUIRED",
    "message": "Read and accept the current privacy agreement to continue.",
    "fields": {},
    "next_action": "accept_privacy"
  },
  "request_id": "synthetic-request"
}
```

| HTTP | Meaning / stable example codes |
| --- | --- |
| 400 | Malformed JSON/multipart request: `INVALID_REQUEST` |
| 401 | Missing, expired, invalid or revoked session: `AUTHENTICATION_REQUIRED` |
| 403 | Disabled account, forbidden role/action, or onboarding gate: `ACCOUNT_UNAVAILABLE`, `FORBIDDEN`, `PASSWORD_CHANGE_REQUIRED`, `PRIVACY_ACCEPTANCE_REQUIRED` |
| 404 | Missing **or inaccessible** individual student/result/report/image: `NOT_FOUND`; do not reveal another person's record exists |
| 409 | Duplicate identity, stale revision, incompatible retry, work in progress: `ACCOUNT_EXISTS`, `STALE_REVISION`, `IDEMPOTENCY_CONFLICT`, `REQUEST_IN_PROGRESS` |
| 413 / 415 / 422 | `IMAGE_TOO_LARGE` / `UNSUPPORTED_IMAGE` / `VALIDATION_FAILED` |
| 429 | `RATE_LIMITED`, with `Retry-After` |
| 500 / 503 | Sanitized `INTERNAL_ERROR` / `SERVICE_UNAVAILABLE`, `MODEL_UNAVAILABLE`, `AGREEMENT_NOT_CONFIGURED`; never expose SQL/configuration details |

The clients refresh an expired Auth session at most once for a recoverable 401, then sign out if still rejected. A 403 onboarding response preserves the session and navigates to its gate; it must not create a login redirect loop. Do not automatically retry writes with a new idempotency key.

Local session/client slice (2026-10-20): login and refresh exchanges are now
explicit public `/session/login` and `/session/refresh` operations, making 33
contract operations in total. The server verifies returned identity and current
profile/access before returning response-only token fields. `/session/logout`
requires a verified bearer but bypasses availability/onboarding gates, commits
durable local-session denial with unapplied migration 008, then calls provider
local sign-out. The new `/access` Vue flow stores tokens in memory only; it may
retry a read once after refresh and never replays password/acceptance writes.
Existing resource clients remain on their MySQL APIs; this is not UUID mapping
or a full cutover. See [session integration](graphiscan/api/SESSION_INTEGRATION.md).

## 2. Identity and onboarding

Supabase Auth handles sign-in, refresh and recovery. Flask verifies access tokens using a supported verifier for the configured issuer/signing keys and checks trusted application records on **every** protected request. Never trust a decoded-but-unverified token, client-stored role, or editable user metadata for authorization. JWT verification establishes identity, not current GraphiScan permissions. [Supabase JWT guidance](https://supabase.com/docs/guides/auth/jwts).

For normal data operations, request checks run in order: valid identity/session → existing active GraphiScan profile → required password change → current agreement acceptance → action permission → record assignment/scope. Bootstrap/onboarding use the restricted state table below; sign-out remains available to a verified session regardless of account/onboarding state. No profile means no application data access, including an Auth account created outside the approved issuance process. Disable public account creation in the target Auth configuration as well as refusing application signup.

Bootstrap `GET /me` remains available before onboarding and returns `user_id`, `full_name`, `role`, `account_status`, granted `permissions`, authorized `school_ids`, and `onboarding`:

```json
{
  "data": {
    "user_id": "00000000-0000-4000-8000-000000000001",
    "full_name": "Synthetic Teacher",
    "role": "teacher",
    "account_status": "active",
    "permissions": [],
    "school_ids": ["10"],
    "onboarding": {
      "must_change_password": true,
      "required_agreement_version": null,
      "accepted_agreement_version": null,
      "next_action": "change_password"
    }
  },
  "request_id": "synthetic-request"
}
```

| State | Permitted application operations |
| --- | --- |
| Invalid/missing session or missing profile | No protected data |
| Disabled/rejected/pending profile | Sign-out and a minimal account-unavailable response; no records |
| `must_change_password=true` | Bootstrap, password change, sign-out only |
| Password changed, agreement not accepted/current | Bootstrap, current agreement, acceptance, sign-out; self password change remains available |
| Both gates complete | Role/permission/scope-authorized operations |

`POST /me/password` accepts `current_password`, `new_password`, `confirm_password`. Verify the current credential, validate strength/match/difference, update Auth, and clear the application flag only after confirmed success. Keep a failed distributed update closed to normal features. The current baseline strength policy is at least eight characters with uppercase, lowercase, digit, and symbol; centrally maintain any future policy change. Resets do not silently clear onboarding flags or invent acceptance.

Local implementation (2026-10-20): this endpoint is now a `foundation` operation. It limits each password to 4096 characters and JSON to 16 KiB (413 when oversized); extra/malformed fields and strength/match failures return 422. A separate optional function-only writer, unapplied migration 006 and durable pending operation protect distributed writes. Uncertain post-begin failures return 503 `PASSWORD_CHANGE_RECOVERY_REQUIRED` and keep access closed. Hosted enablement/verification is pending. See [password setup and recovery](graphiscan/api/PASSWORD_CHANGE.md); production recovery and client integration are separate work.

Password change and sign-out must deny affected old sessions at the API. Do not assume an otherwise valid JWT is immediately unusable after provider sign-out: Supabase documents access-token validity until expiry. Implement and test durable application session revocation/security-version checks alongside provider session operations; the existing in-memory token dictionaries do not satisfy this contract. Reauthentication after a password change must work without a timestamp-boundary lockout. [Supabase session behavior](https://supabase.com/docs/guides/auth/sessions).

`GET /privacy-agreement` returns only approved `version`, `title`, `content`, `published_at`; `POST /me/privacy-acceptance` accepts exactly the currently approved `agreement_version` and `accepted: true`. Record server time, user, and version; repeating acceptance is harmless. A superseded version returns 409 `AGREEMENT_CHANGED`. No approved wording/configuration means 503 `AGREEMENT_NOT_CONFIGURED` and no access beyond the gate. Never use placeholder text as consent.

Temporary test-use implementation (2026-10-20): user authorized a distinct fictional-account notice based on the internal review brief. The notice GET and acceptance operations are now `foundation`. Unapplied 007 supports an optional test subject and atomic session/profile/password/current-version checks plus acceptance/audit. The prepared fixture binds the exact readable test notice to the existing fictional profile; other subjects cannot see/use it as their required agreement. This is test participation acknowledgment, not real-data consent or institutional approval. Revisions publish a new immutable version and require fresh acceptance. Publication/real hosted acceptance are pending; see [privacy setup](graphiscan/api/PRIVACY_ACCEPTANCE.md). Acceptance JSON is limited to 4096 bytes, version to 256 characters; additional fields and non-true acceptance are rejected.

`POST /accounts` requires an administrator or a researcher with an explicit `accounts.manage` grant. Accept `full_name`, normalized `email`, `role`, `temporary_password`, and permitted `school_ids`. The password is write-only, never echoed or logged. Provision an Auth identity and trusted profile with `must_change_password=true`; do not mark issuance complete until both exist. Compensate or reconcile an orphan Auth identity if profile creation fails. Auth administrative account creation belongs exclusively on the server. [Supabase administrative user creation](https://supabase.com/docs/reference/javascript/auth-admin-createuser).

An actor cannot grant a role, school scope, or permission they are not authorized to issue. Permission changes require a separate `permissions.manage` grant; changing the word `role` is insufficient. `PATCH /accounts/{user_id}` may explicitly replace `permission_grants`, an array of `{permission_key, school_id}` objects; null school scope is global. Omission leaves grants unchanged, while an empty array revokes them. Check the actor's grant ceiling and apply the replacement with its account revision in one transaction. Bootstrap `permissions`/`school_ids` are navigation projections, not a substitute for these scoped server records. Bootstrap/admin-recovery procedures and private delivery of temporary credentials require implementation documentation before pilot onboarding.

Account update source implementation (2026-10-21): `PATCH /api/v1/accounts/{user_id}` now accepts revision-checked name, role, account status, school memberships, and permission-grant replacement. The protected SQL capability rechecks current session/onboarding/global `accounts.manage`, enforces role/grant ceilings and school existence, rejects self privilege/scope changes, serializes last-active-admin protection, invalidates affected sessions, and audits the change transactionally. Admin list rows now include account revision; the admin Users page edits name/role/status. `017_account_management.sql` is an unapplied hosted migration and requires a separate function-only `graphiscan_admin_writer` connection. Local synthetic API/SQL checks passed; no hosted account write was performed. Account creation and temporary-password reset remain open.

## 3. Record access and ownership

Permissions and assignments below are server-side records. `GET /me` exposes them for navigation convenience, not as client authority. Grant names are proposed technical identifiers for the already agreed permissions, not implicit powers granted to every researcher.

| Actor | Read boundary | Write boundary |
| --- | --- | --- |
| Administrator | Authorized administrative records | Accounts, schools, assignments and oversight through explicit management grants; not an expert validation by role alone |
| Researcher | Only explicitly granted operations and schools | Only explicitly granted administrative operations; no unrestricted researcher access |
| Teacher | Currently assigned students and their relevant history | Create students in authorized schools, manage permitted links, submit handwriting for currently assigned students |
| Expert | Assigned screenings, student context and history needed for that review | Review only screenings assigned/otherwise explicitly authorized to that expert; cannot rewrite inference |
| Parent | Linked children and **currently Validated** screenings/reports/images | No staff/student/prediction/review writes |
| Guest | Public information, allowed models, isolated demonstration | Demo only; no real student identifiers or official assessments |

School membership alone never grants teacher/expert/parent access to every record at that school. Check current record links after school/teacher/parent/expert reassignment, including downloads and retried requests. `handwriting_samples.teacher_id` records upload provenance; it does not grant a former teacher permanent access after reassignment. Parent totals/history/searches exclude Pending and Flagged records without leaking their classifications or hidden counts.

Parent access is checked against the current review on every read. Moving a review from Validated to Flagged removes subsequent parent access to the result, report and image; retained downloaded copies cannot be recalled by an API. Do not cache released responses in shared caches.

## 4. Resource definitions

| Resource | Required contract fields and constraints |
| --- | --- |
| Account | `user_id`, `full_name`, `role` (admin/researcher/teacher/parent/expert/guest), `account_status`, `revision`, authorized school/permission grants, onboarding state; credential fields are write-only |
| School | `school_id`, nonblank `name`, `revision`, `created_at`; detect normalized duplicate names for review, not a claim of official school identity |
| Student | `student_id`, `full_name`, positive integer `age` on creation (nullable for unknown legacy age), required `school_id`, integer `grade_level` 1–3, active `teacher_id` on creation (nullable after historical unassignment), nullable eligible `parent_id`, `revision`, dates |
| Model | `model_id`, immutable `model_key`/`model_version`, `architecture`, `task_type`, `class_labels`, preprocessing/decision-rule identity, `is_selectable`, `is_default`, evaluation reference; unknown historical metadata is explicit |
| Screening | `result_id`, `student_id`, `sample_id`, `revision`, immutable model/task/decision-rule snapshot, `classification`, nullable `class_scores`, nullable `predicted_class_score`, `date_generated`, `report`, current `review`, provenance |
| Report | `report_id`, `result_id`, `student_id`, `report_type`, screening date, school/grade context, model/task/scores, current review; JSON representation in this baseline, not a promise of PDF export |
| Review | `status`, nullable `assigned_expert_id`, nullable `expert_id` of the actual reviewer, `remarks`, nullable `expert_recommendation`, boolean `follow_up_needed`, `validation_date`, `revision`; append protected review revisions instead of erasing prior decisions |

For student creation by a teacher, derive `teacher_id` from identity; reject an attempt to assign a different teacher. Admin assignment changes validate current active roles and authorized schools. Parent eligibility/link verification must use trusted assignments, not a client-supplied role or a global public account directory. Parent/teacher option responses contain the minimum identifiers/display names authorized for that assignment action.

Duplicate student names are a review warning within school/grade, not proof of the same child. Avoid silently merging children. Mutating a school/student/account/assignment/review requires its current `expected_revision`; a stale write returns 409 without overwriting another actor's changes. Expert assignment updates check the screening revision and advance both screening and current-review revisions, so an old review form cannot submit after reassignment. Changing assignment must not overwrite the identity/date of the expert who authored an existing decision. Student/role/school assignment changes likewise advance the resource revision used by their update endpoint.

School/student mutation implementation: global schools.manage is required to
create a school; scoped grants can update their school. Administrative student
changes require assignments.manage in source/destination schools, active teacher
membership and explicit assignment eligibility; teacher creation derives self
and requires school membership, and teachers cannot transfer schools/teachers.
Parent links require current eligibility; null clears the link. JSON is bounded
to 8 KiB, names 200 characters, age to positive smallint storage range and
revisions to positive int64. Mutation responses add optional warnings containing
only duplicate_name, checked within actor-readable scope. Student creation uses
durable actor/key mappings and database-held HMAC digests; replays reauthorize
and return current metadata. Mappings do not automatically expire. See
[mutation setup and limits](graphiscan/api/DIRECTORY_WRITES.md).

### Scores and historical models

`class_scores` uses keys `normal`, `high_potential`, and, for three-class models only, `low_potential`. Values are model outputs, not calibrated clinical probabilities. Full normalized scores must correspond to that model's class mapping; missing historical scores remain `null`. `predicted_class_score` means the score of the reported class, **not necessarily the maximum score** when a threshold decision rule is used.

For example, current predictor source reports Normal for a High Potential score of 0.60 because its cutoff is 0.75. Its reported-class score is then 0.40. The migration must preserve that decision instead of recomputing an argmax. This example comes from source logic, not a newly run inference:

```json
{
  "task_type": "binary",
  "classification": "Normal",
  "class_scores": {"normal": 0.4, "high_potential": 0.6},
  "predicted_class_score": 0.4,
  "decision_rule": {"kind": "high_potential_threshold", "threshold": 0.75}
}
```

Do not compare the existing binary accuracy with experimental three-class accuracy. A selectable three-class model needs a documented common evaluation/split and per-class evidence. The default is the highest evaluated accuracy among the eligible models on that same task/evaluation, not among unrelated historical reports. Do not invent a tie-break; deployment configuration must select one default before enabling a tied set. The API pins the resolved model/version when accepting a request; a later default change cannot rewrite that assessment.

For legacy records, preserve original labels and verified percentage-to-fraction conversions. If model/version or score meaning cannot be established from evidence, mark provenance `legacy_unverified`, model/version as unknown in the API, and unavailable derived scores as `null`. An explicitly identified unselectable legacy registry row can satisfy the database FK; it must not imply a verified artifact. Never label binary Normal as Low Potential. Omit obsolete AI advice and canned analysis; attribute any recommendation to the expert and review date.

## 5. Endpoint catalogue

All paths below are relative to `/api/v1`. OpenAPI marks implemented operations `foundation`; remaining operations are proposed. Onboarding and scope checks apply to all protected routes, including list, summary and image routes.

Directory GET implementation: administrative student access requires scoped
`assignments.manage`; school-directory grants accept `accounts.manage`,
`schools.manage` or `assignments.manage`. Teacher student links, parent links
and current expert screening assignments establish their student context scope.
Teacher school memberships additionally allow school-directory selection, never
access to other students. Search is a literal substring, limited to 120 characters;
unknown or duplicate query parameters return 422. Signed cursors bind to the
actor/session/resource/filters/limit, expire after 30 minutes and on process
restart, and use descending created_at/numeric ID keysets. Current scope is
rechecked on each page. No unfiltered counts or result data are returned.
See [directory setup and limits](graphiscan/api/DIRECTORY_ACCESS.md).

Screening GET implementation now covers list/detail, student history and report
JSON through a function-only reader capability in prepared migration 012 (not
yet applied to the hosted project). Current student links scope teachers/parents;
parents require current Validated review before pagination; experts require the
individual screening's current assignment. Admin/researcher reads use scoped
assignments.manage. Historic model identity comes from the frozen result
snapshot; unverified identity stays unknown. See
[screening read setup and limits](graphiscan/api/SCREENING_READS.md). This does not
implement upload, review mutation or private image access.

| Method / path | Contract / access |
| --- | --- |
| `GET /health` | Public minimal service status; no configuration, accounts, database names or model filesystem paths |
| `POST /session/login` | Public email/password exchange; return tokens only after provider identity/current issued active profile verification |
| `POST /session/refresh` | Public refresh-token exchange; verify returned identity/current access before returning rotated tokens |
| `GET /me` | Bootstrap profile/onboarding state; restricted account status response when unavailable |
| `POST /me/password` | Password change flow above; secrets never returned |
| `POST /session/logout` | Revoke current application/provider session; clear local client state even on transport failure |
| `GET /privacy-agreement` | Current approved agreement, subject to the onboarding order |
| `POST /me/privacy-acceptance` | Current-version acceptance after password gate |
| `GET /accounts` | Implemented hosted read-only list with global `accounts.manage`; filters `q`, `role`, `account_status`; signed cursor pagination |
| `POST /accounts` | Admin-issued temporary account; returns account metadata only |
| `PATCH /accounts/{user_id}` | Authorized profile/role/status/school changes with `expected_revision`; explicit `permission_grants` replacement additionally needs `permissions.manage`; protect own/last active admin and grant ceilings |
| `POST /accounts/{user_id}/temporary-password` | Authorized temporary reset with write-only `temporary_password` and `expected_revision`; require first change again, revoke old access, retain agreement history |
| `GET /schools` | Actor-authorized school directory; guest has no private student summaries |
| `POST /schools`, `PATCH /schools/{school_id}` | `schools.manage`; nonblank name; revision on update |
| `GET /schools/{school_id}/assignment-options` | Minimum eligible teacher/parent/expert identities for an explicitly permitted assignment operation; no unrestricted account search |
| `GET /students` | Authorized student list; filters `q`, `school_id`, `grade_level`; teacher/parent filters cannot widen actor scope |
| `POST /students` | `full_name`, `age`, `school_id`, `grade_level`, `teacher_id` for authorized admin assignment, optional `parent_id`; derive teacher actor's own assignment |
| `GET /students/{student_id}` | Authorized identity/context; no provisional parent data |
| `PATCH /students/{student_id}` | Permitted profile/link changes plus `expected_revision`; assignment changes need management authority |
| `GET /models` | Allowed model metadata/selectable/default state; no model weights or private paths |
| `POST /screenings` | Teacher-only official multipart upload, completed assessment returns 201 |
| `GET /screening-requests/{idempotency_key}` | Submitting actor's request state: `processing`, `completed` with authorized result reference, or `failed`; no access to another actor's key |
| `GET /screenings` | Role-filtered list; allowed filters `student_id`, `school_id`, `grade_level`, `validation_status`, `model_id`, `task_type`, date range; parent projection always Validated |
| `GET /screenings/{result_id}` | Authorized detail with model/version, dated report and current expert state |
| `GET /students/{student_id}/history` | Authorized dated assessments; parent release filtering before pagination/counts; no automatic improvement claim |
| `PATCH /screenings/{result_id}/expert-assignment` | Explicit assignment-management authority, active eligible `assigned_expert_id` or null to unassign, screening `expected_revision`; audit reassignment |
| `PATCH /screenings/{result_id}/review` | Assigned expert only: `status` Validated/Flagged, nonblank `remarks`, optional `expert_recommendation`, boolean `follow_up_needed`, `expected_revision` |
| `GET /reports/{report_id}` | Authorized report JSON; parent link + current Validated decision required |
| `GET /screenings/{result_id}/image` | Reauthorized image stream, private storage; no arbitrary storage path accepted |
| `POST /demo-screenings` | Enabled guest demo only; multipart image/model, no student ID, no official rows/report |
| `GET /summary` | Authorized counts grouped by school/grade/review as permitted; parent totals include released records only |
| `GET /audit-logs` | Implemented hosted read-only list with global `audit.read`; filters `q`, `role`; signed cursor pagination; no credential/private payload logging |

Permanent-delete routes are deliberately **unresolved**, not silently converted to archive or cascades. Current MySQL admin routes delete linked rows/files; the target PostgreSQL draft uses `ON DELETE RESTRICT`. Decide retention, deletion authority, audit preservation, reauthentication and restore implications before specifying or implementing v1 deletion. Existing routes remain unchanged by this document. Model publication/default changes likewise remain controlled deployment actions until the evaluation registry is ready; a model selector does not authorize weight uploads from clients.

## 6. Upload, retry, and assessment transaction

`POST /screenings` accepts multipart `student_id`, optional `model_id` (resolve the current eligible default if absent), and `handwriting_image`. `POST /demo-screenings` accepts only image/model. Verify actual image format/decodability, byte and decoded-pixel limits, and the permitted JPG/PNG formats; a filename suffix is insufficient. Server-generated object keys must not contain student names or trust an upload filename. Publish configured upload limits with model/client configuration before enabling capture; concrete limits require device/host testing rather than an invented promise here.

Official screening, student/account creation and review writes require an `Idempotency-Key` generated once per logical action (16–128 ASCII letters/digits/underscores/hyphens, such as a UUID). Bind keys to actor, operation and a protected request digest; do not store plaintext password bodies. Same actor/key/payload replays the completed authorized result; changed payload returns 409, processing returns 409 `REQUEST_IN_PROGRESS` plus `Retry-After`. Recheck current authorization on replays. Preserve completed screening-key mappings for as long as their official result is retained. Define retention for other keys during implementation; expired keys must not silently duplicate credential issuance or an assessment.

Pipeline:

1. Verify session, gates, student ownership and model eligibility; reserve the actor's request key durably.
2. Validate/store the image privately and pin immutable model/preprocessing/decision-rule identity. Run inference outside a long-held student database lock. Demo work uses isolated temporary storage and never official tables.
3. For an official success, open a transaction, recheck access/model validity, and lock the student's authoritative row. Determine Initial versus Follow-up from completed official reports under that lock. Insert sample, result, Pending review, report, idempotency completion and audit together. Keep the unique Initial-per-student index as an additional invariant; the index alone does not perform the assignment.
4. Return 201 only after commit. Validation/inference/database failure leaves no official partial assessment. Compensate private object writes on failure, with durable cleanup/reconciliation if storage deletion itself fails. Do not delete/reuse an existing official object on a retried key.

The first completed official assessment is Initial; concurrent later completions are Follow-up. A disconnected/cancelled HTTP client does not prove the server rolled back: retain the same key and query request state before resubmitting. The baseline is synchronous completion with a recovery lookup; a 202 background-job protocol is not implicitly implemented. Hosted request/inference timeouts and the paper's response target need measurement.

## 7. Private image and report release

Baseline delivery is a Flask-authorized binary stream from a **private** Storage bucket. Vue/Expo request the image with the current bearer credential and handle blobs/local temporary files; do not construct static upload URLs or put a bearer token into `<img src>`. The server derives the storage object from the authorized result ID, then checks role, current assignment, onboarding and, for parents, current Validated status. Do not include storage object paths in normal client result JSON.

Private buckets support controlled authenticated access and expiring signed URLs, but those are different delivery mechanisms. This baseline chooses the API proxy so each new read can recheck release status. Adopting signed URLs later needs an explicit expiry/revocation contract; they must not be described as immediately revoked merely because a review changed. RLS remains enabled, no public student bucket or broad client table policies, and elevated server credentials are never bundled into a client. [Supabase private bucket behavior](https://supabase.com/docs/guides/storage/buckets/fundamentals), [Storage access control](https://supabase.com/docs/guides/storage/security/access-control).

## 8. Current-to-target migration map

| Observed current source | Target contract / required work |
| --- | --- |
| Separate `/api/admin/*` and role-prefixed `/api/user/*`; localStorage bearer helpers | Shared `/api/v1` resource routes and explicit adapters; do not redirect existing POST bodies into a new schema |
| Process-local tokens, admin-only current-status refresh | Verified Auth identity plus durable session/account/gate checks for every role and protected path |
| Numeric MySQL users; `fullname`, grade strings, `Yes`/`No`, percentage scores | UUID identity mapping; `full_name`, grade integers, booleans and verified fraction conversions |
| No student school; identity draft has no permission/membership tables | Trusted permissions and school memberships, eligibility/assignment checks and migration reconciliation |
| Expert paths can address general results; review API currently requires a recommendation | Enforced expert assignments; required remarks and optional human recommendation, matching the target design |
| Predictor uses one binary artifact and 0.75 High Potential threshold | Pin version/decision rule; preserve binary history; add evaluated three-class selection only when supported |
| Count-based Initial label; no request-key registry | Serialized completion, unique Initial constraint, durable idempotency/request recovery and storage compensation |
| Local `static/uploads` and image URLs; old Flask/session pages remain | Private objects and authorized streams; migrate or retire every bypassing legacy route before cutover |
| One current validation row and free-text audit entries | Current state plus protected immutable review revisions and transactional structured audit |
| Admin cascade deletes vs PostgreSQL RESTRICT drafts | Resolve retention/deletion semantics before v1 deletion; do not silently change existing behavior |

The original two PostgreSQL files alone are insufficient for this contract. [003_api_contract.sql](graphiscan/db/postgres/003_api_contract.sql) now drafts storage and constraints for permission grants, school memberships/eligible assignments, expert assignment, resource revisions, request keys/statuses, agreement publication/configuration, session revocation/security version, review history, structured audit columns, model evaluation/provenance/decision-rule metadata and cleanup jobs. It was tested with fictional records in isolated PostgreSQL, not deployed. Handlers still must enforce authorization, credential lifecycle, transactional audits, snapshot completeness, current release state, recovery and storage compensation; enabled RLS and schema validation do not implement those behaviors.

## 9. Acceptance gates and implementation order

1. Review the accompanying OpenAPI draft and proposed integration cases; resolve each policy input before its dependent behavior. Offline schema/payload tests now run, but live v1 access tests still require implementation. The contract is not yet a frozen client interface.
2. Review 001/002/003 in a disposable Supabase test project and extend migration mappings/rollback evidence. The local PostgreSQL checks do not substitute for hosted Auth/Storage/role validation. No production row imports during contract work.
3. Implement identity/bootstrap/password/privacy and durable authorization first, including restricted-key/private-storage boundaries. Verify current SDK/provider integration details when writing code.
4. Implement schools/assignments/students, then model/history/upload transactions and expert release; adapt Vue in slices, retaining current-stack recovery.
5. Build the Expo shell against the stable tested slice, then complete remaining roles. Do not point real clients at partly migrated records.

Required tests include: unknown/disabled/demoted identities; every onboarding bypass; wrong-school/teacher/parent/expert IDs; forged client roles and permissions; unvalidated parent list/detail/history/summary/image denial; revocation after assignment/review/password/logout changes; nullable unknown legacy provenance; fractions/thresholds/class sets; stale reviews; duplicate/retried/concurrent uploads producing one Initial; failed inference/storage/commit producing no official partial row; demo isolation; schema/data/image reconciliation and rollback. Run authenticated desktop/phone/admin/Expo checks after adapters, not just contract parsing.

Inputs still open: approved privacy text/version; retention/permanent-delete policy; school and participant mapping/verification; authorized researcher/grant owners and expert assignments; evaluated model evidence/default/tie decision; measured upload/timeout limits; and test Supabase/hosting/device access. These gate their dependent implementation. No missing policy is treated as approved merely because a technical endpoint is proposed.
