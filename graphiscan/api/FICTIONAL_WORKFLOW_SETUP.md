# Hosted fictional workflow setup — applied and preflight verified

User reported atomic015 success on2026-10-20. Agent ran the restricted read-only
setup checker: all23 checks passed, with no database writes. Updated API5002 is
active(session43462), health200/admin/access200/protected anonymous401. This
preflight covers metadata/profile/notice/grant/membership scope, not populated
student/eligibility APIs or end-to-end upload/review/release. Passwords stay private.
XAMPP repair/legacy cleanup is stopped; the legacy files are archived, not deleted.

**Do not rerun015_workflow_fixtures.sql, its sources or001–014.** Next freshly
sign in to admin/access with the current admin password, explicitly accept the
new notice and check the synthetic school/student. No admin password reset.
Then onboard each new user through hosted Expo. The seed source is a builder
template; generated bundle is retained for reviewed fresh setup only.

Verification:162 v1 Python tests and114 isolated PGlite checks passed using the
actual bundle and reader SQL, including rollback, scope, compatibility, immutable
notice audience, forced password/consent gates and role ACLs. Local assertions
and hosted read-only preflight are separate evidence; neither proves a real
end-to-end role flow.

The next populated hosted check needs actual issued identities and current
record scope. The existing Synthetic Test Admin has no automatic management
grant; its current `graphiscan-test-v1` notice applies only to that account.
Do not clear its audience field, insert acceptances, reuse MySQL identities,
or reuse an existing person's account to bypass setup.

## Exact proposed fixtures

| Identity or record | Proposed scope |
| --- | --- |
| Existing `graphiscan.test@example.invalid` / Synthetic Test Admin | Retain identity and password state; explicitly grant `assignments.manage` for the one synthetic school only |
| `graphiscan.teacher.test@example.invalid` / Synthetic Test Teacher | New active teacher profile, forced first-password change; membership in that school; assigned teacher for the synthetic student |
| `graphiscan.expert.test@example.invalid` / Synthetic Test Expert | New active expert profile, forced first-password change; school membership; eligible expert choice for that admin in that school |
| `graphiscan.parent.test@example.invalid` / Synthetic Test Parent | New active parent profile, forced first-password change; linked parent for the synthetic student |
| GraphiScan Synthetic Workflow School | New fixture school; no existing school reused or renamed |
| Synthetic Workflow Student | New fictional student, age8, grade2, linked only to the specified teacher/parent and synthetic school |

The admin's eligible teacher/parent choices will be restricted to those two new
profiles in the synthetic school. The teacher's eligible parent choice will be
restricted to the fictional parent in that school. No global grant, `accounts.manage`,
`permissions.manage`, `schools.manage` or `audit.read` grant is proposed. No teacher,
expert or parent receives an admin capability. The expert is assigned to each
screening through the existing admin UI, rather than granting access to every
result merely through school membership.

The owner-run setup would create the single school/student fixture because the
admin is deliberately not being given a school-creation privilege. Setup must
resolve each exact Auth email to exactly one identity and reject existing or
conflicting profiles/fixtures. It must not reset existing passwords or silently
attach to an existing school/student. This SQL package is implemented and
checked in the generated atomic bundle; it has not run hosted.

## Notice proposal and engineering dependency

Review [the separate final test-notice text](fictional-workflow-notice.txt). It is
for only these four explicitly identified fictional accounts and this exercise.
It is not real-user policy wording or permission to use real student records.

Observed source constraint: `003_api_contract.sql` allows one current notice
globally. `007_privacy_acceptance.sql` adds a single `test_subject_id`; the notice
read in `v1_privacy.py`, bootstrap in `access_snapshot.sql`, and the database gate
in `009_directory_reads.sql` all enforce that single-account audience.
Screening read/write gates reuse the directory gate. A text-only notice swap
cannot safely onboard all four roles under the existing single-subject setup.

Prepared implementation: add explicit bounded multi-account test audience
support while preserving existing single-account and ordinary notice behavior.
Publish a new version restricted to the four exact fixture IDs only after
review. Keep the original notice text, audience and acceptance rows intact;
publishing the replacement retires its current flag. The existing admin
must explicitly accept the new version too. This behavior is prepared locally,
not yet applied. Do not set `test_subject_id` to NULL as a shortcut
to making the old notice apply to everyone.

Passing isolated tests cover bootstrap, notice read, acceptance and database resource gates
for allowed/foreign identities, changed versions, empty/malformed audience,
single-subject compatibility, and absence of anonymous/direct client grants.
The old notice content/audience is unchanged. No test acceptance is seeded.

## Execution order after review

1. User reports the three named Auth users created with confirmed test emails.
   Do not recreate/reset them. Never put passwords in SQL, templates or chat.
2. Apply only015_workflow_fixtures.sql once. Missing/unconfirmed/banned/deleted
   identities, existing role profiles/fixtures/scope or differing current notice
   abort the entire transaction. An accidental repeat refuses without overwrite.
3. Agent runs `tools/check_v1_workflow_setup.py --connect` (read-only existing
   restricted reader, booleans only). It checks metadata and reader-visible
   profile/notice/grant/membership scope, not populated student reads or writes.
   After passing, restart ONLY the hosted API5002; do not change API/model/Storage
   credentials or restart unrelated services. No XAMPP is needed. Do not sign in
   for role testing until the updated API is running.
4. Each new role signs in through Expo hosted mode, changes its temporary
   password, then explicitly accepts the exact new notice. The existing admin
   accepts the new version in `/access`; no admin password reset is needed.
5. Teacher uploads a generated test PNG; confirm an Initial Screening. Admin
   assigns the one eligible expert. Expert submits explicitly fictional remarks
   and a Validated review. Parent then reads the released result/report/image.
6. Confirm a later Flagged review denies subsequent parent detail/report/image;
   verify a second upload is a stored Follow-up Screening. Check retries and
   changed assignments without fabricating records or bypassing server scope.

Application of the bundle writes synthetic application fixture/audit data and
retires the old notice current flag. It also invalidates existing admin sessions
through the existing grant trigger. No admin password reset is needed. Actual
application and upload/review/Storage steps have not run. Record observed results.
Native camera/sharing, real multi-connection concurrency, production deployment,
real-data policy and the planned three-class model remain separate work.
