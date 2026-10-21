# Workspace directory screens and assignment choices

Latest live evidence (2026-10-20): user reported no error after Refresh lists;
both authenticated school and student GETs returned 200 in API67766 logs. A prior
school 503 did not recur on this retry; its root cause was not captured. Safe
SQLSTATE-only diagnostics remain. Failed loads now show records-not-loaded,
and both lists load independently with a persistent Refresh lists control.
This confirms scoped reads, not populated forms or write flows. No permission,
credential or database-record change occurred during this verification.

Implemented locally on 2026-10-20. Both existing /access wrappers now render the
shared HostedDirectory.vue after account readiness. The established green form
styles/navigation are extended; legacy dashboards and MySQL clients are unchanged.
Hosted credentials remain in the existing memory-only client and are never sent
to legacy APIs. Reload/sign-out still clears the session and in-memory forms.

## Available interaction

Schools and Students views provide scoped lists, loaded-row counts and Load more
pagination. Student filters are literal name search, school and Grade 1–3; next
pages retain the filters actually submitted, even if filter inputs are later edited.
Teacher/admin-authorized forms create/edit students; school management forms use
the bootstrap permission projection for visibility, with actual grants enforced
by SQL. A school-scoped grant may show Add school but the server requires a global
grant for creation and can deny it. The UI cannot infer global scope from the
existing bootstrap permission list. No role name grants extra API authority.

Parents/experts see authorized identity/context details without edit controls.
Forms load the current student detail/revision before editing. Stale edits retain
the draft and offer explicit reload; school conflicts reload the list so the user
reselects a current record. Failed saves retain inputs. Duplicate warnings use the
server's scoped warning without exposing other record details. Screening uploads,
reviews, reports and historical migrated data are not connected by this slice.

The client now optionally returns list/warning envelopes and sends Idempotency-Key.
It retains its bounded read-only refresh/retry rules; no write is automatically
replayed. New student submissions retain an immutable payload/key in memory after
uncertain errors. The form freezes for an explicit same-submission retry. Validation
rejections allow corrections/new keys. SPA route navigation is blocked while a
submission is unresolved, and beforeunload warns for pending creation/school saves.
Sign-out remains available. Reload/sign-out discards recovery state; check existing
records before creating again after leaving an uncertain submission. This is not
durable client recovery or proof of hosted distributed retry behavior.

School creation is not idempotent in this contract. Uncertain school-create errors
disable resubmission and offer list refresh for manual confirmation instead of
replaying the write. There is no automatic duplicate merge.

## Assignment options

GET /api/v1/schools/{school_id}/assignment-options is implemented locally. New
Installed 011_assignment_options.sql grants only the existing reader one fixed-path
STABLE definer read function. No login, password, accounts, eligibility, grants or
records are seeded. Current session/onboarding is rechecked in the fetch statement.

Teacher membership permits self and explicitly eligible active parents. Admin/
researcher callers need assignments.manage within that school; candidates must be
explicitly eligible and active, with school membership for teacher/expert roles.
No public account search, email or inactive profile is returned. Data has only
user_id/full_name/role. Ordering uses creation time plus UUID; internal time is
used for a signed user/session/school/limit-bound cursor, not exposed as a data
field. Cursors expire after 30 minutes/API restart and use the prior process-key
limitations. Options do not grant eligibility or establish guardian verification.

## Setup and verification

User reported 011 applied after 001–010 in the same disposable project. All ten
independent hosted read-only metadata/zero-identity checks passed. API5002 was
restarted; health 200, unauthenticated options 401 and admin /access 200 passed.
No repeat setup is needed. Actual authorized candidate data/form behavior still
requires verification. The fictional admin has no automatic management grant;
empty lists and hidden forms may be correct. No privilege is auto-granted to make
the screens populated.

Passed: 156 Python tests, 11 JavaScript tests, 494 contract checks, 284 isolated SQL
checks and both Vue production builds. New evidence includes five option service/
HTTP tests, 19 real-function SQL scope/projection/pagination cases and creation
recovery/envelope tests. Both /access pages and shared directory modules returned
200 through their live Vite servers. Browser connector inventory returned no apps/
browsers, so desktop/mobile visual, keyboard and live authorized form checks remain
unverified. No hosted records/credentials/grants were changed by this slice.
