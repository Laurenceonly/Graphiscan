2026-11-06 activation checkpoint:027 is now installed and independently read-only verified (all seven preflight flags true; lookup source matches). Do not rerun it to resume. Matching API/client deployment and real hosted/native parent-link acceptance remain pending. This supersedes unapplied statements below.

2026-11-06 correction: use the updated027 file, which normalizes both sides of its exact source guard for LF/CRLF SQL editor formatting. The previous failed attempt left the hosted writer unchanged and lookup absent in read-only metadata. Copy the full corrected file again before retrying; the guard still rejects unexpected semantic changes.

# Teacher parent linking

Implemented locally on 2026-11-06; migration027 and matching API deployment are
required before live use. No hosted migration or real parent link was performed.

In the Expo Add/Edit student form, choose the school/grade, enter the existing
parent's full login email, choose Find parent, confirm the matched name with
Select parent, then Save student. Remove parent link takes effect only on save.
The parent account is still issued by the admin. One parent may have multiple
linked children, including children in different schools.

The retained hosted Vue teacher form supports the same exact-email lookup. Its
admin/researcher controls are unchanged. The older MySQL/Flask teacher creation
flow already accepts an existing active parent; it was inspected and remains
unchanged. This feature concerns the shared Supabase v1 flow, not a legacy-data
migration or new authority for teachers to create accounts.

## Server behavior

- GET /api/v1/schools/{school_id}/assignment-options accepts parent_email with a
  required grade_level. It is teacher-only, requires the teacher's current school
  membership and grade, and returns zero or one matching active parent by exact
  normalized login email. It exposes only user_id, full_name and role. It cannot
  be used with a cursor, partial names, or a broad parent-directory query.
- POST /api/v1/students and PATCH /api/v1/students/{student_id} retain their
  existing parent_id field. Migration027 removes the teacher-only parent-change
  prohibition while preserving ownership, school/grade, current-session,
  onboarding, active-parent, revision, idempotency and transactional audit checks.
  Teachers may link, replace or clear a parent only for their own authorized
  students. A parent can be newly issued and still require onboarding before that
  parent can access records. Credential-update-pending/disabled/non-parent
  candidates cannot be linked. No teacher or school reassignment is allowed.
- Discovery does not grant record access or reserve a link. The selected parent
  and student's authority are checked again at save. A known parent ID may also
  be used by an authorized teacher; exact-email lookup limits directory exposure,
  rather than serving as a separate write permission. The database uses the
  student's current parent_id on each read; replaced/unlinked parents lose access.
  Parent screening/report release remains Validated-only.

## Activation

1. As the database owner, run db/postgres/027_teacher_parent_linking.sql after the
   already-installed026. It changes functions/grants only and creates no people,
   student links, passwords, consent or school/grade assignments. Exact reruns
   preserve the installed writer; unexpected writer bodies fail transactionally.
2. Run db/postgres/027_teacher_parent_linking_preflight.sql. All seven metadata
   flags should be true. This check reads no account/student data.
3. Publish/restart the matching Python API (v1_assignment_options.py). Local Expo
   normally calls the hosted API, so a local source change alone is insufficient.
   Refresh Expo after the API is available. The retained Vue teacher client needs
   its corresponding web build deployed if it is used for this flow.
4. In a controlled teacher session, add/edit an owned student and link a fresh
   parent. Check parent sign-in/onboarding, the linked child, and Validated-only
   reports; then test replacement/removal. These real hosted/native checks remain
   pending and must not be inferred from fixtures.

## Verification

Nine focused Python API tests,654 contract assertions and all isolated SQL suites
pass, including62 new parent-link checks covering permissions, scope, parent
eligibility, replays, revisions, access after replacement/removal, audit rollback,
migration rerun and installation metadata. Both Vue builds, Expo TypeScript/20
mobile tests and Android/web exports pass. Fictional mobile browser checks cover
lookup failure/retry, explicit selection, creation, replacement and removal at
320/390. This is separate from real hosted/native acceptance.
