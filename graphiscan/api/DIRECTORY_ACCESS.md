# School and student read access

Implemented locally on 2026-10-20. This adds `GET /api/v1/schools`,
`GET /api/v1/students` and `GET /api/v1/students/{student_id}`. It does not
implement student/school creation, updates, assignment options or a new record UI.

## Authorization

Every request verifies the bearer, active profile, password and current notice
acceptance through the existing guard. The restricted database read function
repeats session existence/expiry/revocation/security-floor checks, active-account
and onboarding gates and current record assignments in the statement fetching
the records. A change between the guard and query therefore cannot retain a
stale permission from the first check. A later transaction takes effect on the
next read; this is not a claim of distributed instantaneous revocation.

- Teachers see students whose current `teacher_id` matches their verified subject.
- Parents see linked children; this endpoint returns identity/context, no result
  labels, review counts, hidden screening totals or image paths. Result/report
  access still requires its own current Validated release check when implemented.
- Experts see student context only where a screening is currently assigned to
  them through `screening_expert_assignments`. Authorship of an old review alone
  does not grant access.
- Admin/researcher student reads require `assignments.manage`, globally or for the
  student's school. Role names and school memberships alone do not grant them
  student access. School-directory reads accept scoped `accounts.manage`,
  `schools.manage` or `assignments.manage` grants.
- Teachers may list their membership schools to support later student creation,
  and schools for their currently assigned students. Parents/experts see schools
  for their linked/assigned student context. Membership alone does not widen
  student access or the parent/expert/researcher school directory. Guest is denied.

Missing and inaccessible student details both return 404. Empty scoped lists
return 200 with an empty array. All responses use `Cache-Control: no-store`.

## Filtering and cursors

Lists accept `limit` (default 25, 1–100), `cursor` and `q` (at most 120 characters,
case-insensitive literal substring). Student lists also accept `school_id` as a
canonical positive int64 string and `grade_level` 1–3. Unknown/duplicate query
keys, control characters and invalid identifiers/limits return 422. Detail reads
accept no query parameters. IDs remain strings across the wire.

Scope and filters apply before keyset pagination. Ordering is descending
`created_at`, then numeric ID, with one lookahead row for `next_cursor`.
No unfiltered counts are returned. Cursors bind to the user, session, resource,
normalized search, school/grade filters and limit, using HMAC-SHA256. They expire
after 30 minutes; the next request rechecks current assignments and gates.
The signing key is random process memory: restarting the API invalidates cursors.
Multiple independently keyed workers are not supported by this cursor setup;
shared-key configuration/rotation would need a separate deployment change.
Cursor contents are encoded, not encrypted; treat them as opaque navigation
values, not credentials. Do not log full authenticated URLs or search terms.

## Disposable hosted setup

Migration **009_directory_reads.sql is user-reported applied** after 001–008
in the same disposable project. Do not rerun it. It grants the
existing private reader EXECUTE on one fixed-path SECURITY DEFINER SQL function.
It adds no table grants, login/password, application rows or data import. Public,
anonymous, authenticated, service-role and password-writer execution is revoked.
The function uses a bounded page size and allowlisted JSON projection.

No new credentials, Auth reset, notice acceptance or seed is needed. All 15 hosted
read-only metadata/zero-identity denial checks passed. Updated API5002 is running;
live health returned 200 and all three directory routes returned 401 without a
bearer, after superseded Python processes were stopped. Authenticated hosted
role-scoped record requests remain unverified. The existing fictional
admin has no automatic student-management grant; an empty directory can be the
correct result. Do not invent real student data or silently grant privileges to
populate a screen. New Vue resource screens and record writes remain later work.

## Verification

The full Python suite passed **140 tests**, including 11 new HTTP/service tests.
OpenAPI validation passed **494 checks**; isolated SQL passed **210 checks**,
including 45 new directory checks executing the real function with fictional
Auth/records. These cover private grants, scope/filter intersections, literal
search, keyset ties, reassignment, fresh gates and session denial. This is local
evidence, not a hosted resource or browser-directory test. Prior seven JS-client
tests and both Vue builds are unchanged evidence from the preceding slice;
no frontend source changed in this slice.
