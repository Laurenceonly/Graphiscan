# School and student mutations

Implemented locally on 2026-10-20: POST /schools, PATCH /schools/{school_id},
POST /students and PATCH /students/{student_id} under /api/v1. Existing
session/account/password/current-notice gates apply. Management screens,
assignment-option queries and account issuance are not added by this slice.

## Authorization and transaction

School creation requires global schools.manage; edits require that grant globally
or for the target school. Admin/researcher role alone is insufficient. Student
administrative writes require assignments.manage for both original and destination
schools when moving a student. Teachers create students only in their current
school memberships, deriving teacher_id from verified identity. A supplied different
teacher is rejected. Teachers edit their currently assigned students in membership
schools, but cannot transfer schools or assign another teacher. Parents, experts
and guests cannot write these resources.

Teacher candidates must be active teachers with destination-school membership.
Administrative assignment also requires a matching actor/candidate/school/teacher
assignment_eligibilities row. Parent links require an active parent and matching
actor/candidate/school/parent eligibility. This is trusted administrative eligibility,
not automatic guardian identity verification. Null clears a parent link. Existing
historical null teacher links may remain null on edit; creation requires a teacher.
No endpoint grants permissions, membership or eligibility.

The fixed-path definer function takes SHARE locks on actor/candidate profiles,
the current notice and applicable eligibility, and UPDATE locks on target records.
Existing security/grant/membership triggers update actor profiles, serializing
against those locks. The function repeats session, gates and record scope checks.
It does not modify Auth tables or require Auth UPDATE privileges. Stale
expected_revision returns 409; existing triggers advance revision/update time.
Record, creation retry mapping and audit commit together. Audit failure rolls back
the operation. Actual hosted concurrency/failure recovery remains unverified;
isolated tests do not establish instantaneous distributed revocation.

## Inputs and warnings

JSON is bounded to 8 KiB. Unknown fields/query parameters are rejected. Names
normalize whitespace, reject control characters and permit 1–200 characters.
Age is a positive smallint, 1–32767 (a storage bound); grade is 1–3. IDs are
positive int64 strings, UUID links are validated, and revisions positive int64
integers. Invalid/missing fields return 422. Creates return 201 with Location;
edits return 200. All responses remain no-store.

Mutation responses include warnings: [] or ["duplicate_name"]. School matches are
limited to actor-managed school scope; student matches to the same school/grade
and actor-readable students. Warnings expose no other identity/count and never
merge children or establish identity.

## Student creation retries

POST /students requires an Idempotency-Key: 16–128 ASCII letters/digits/underscores/
hyphens. Keep the same key/payload after a timeout. A transaction advisory lock
serializes same-actor/key requests. The completed mapping, insert and audit commit
together. Changed payloads return 409. Keys are actor/operation scoped and have no
automatic expiry; retain mappings while their students are retained. Deletion and
cleanup policy remain separate work.

Native SHA-256 HMAC covers canonical JSON with a random database-held key, initialized
once in a private RLS table. Application roles cannot read the key or invoke its
digest helper. It survives API restarts. No plaintext body is retained in request
mappings. Replays reauthorize and return current metadata without another insert
or audit. Former teachers cannot recover reassigned children through an old key.
Successful replay retains creation status 201.

## Hosted setup and evidence

010_directory_writes.sql is user-reported APPLIED after 001–009 in the same
disposable project. Do not repeat it. It reuses graphiscan_password_writer and
existing connection setting; this role now serves reviewed directory mutations
alongside onboarding/session operations. No new login/password is needed.
One private key table, two inaccessible helpers and one writer-executable mutation
function are added. Reader/client/service roles cannot execute mutations; no direct
resource/request/audit write grants are added. No application accounts, records,
memberships, grants or eligibilities are seeded. Do not grant privileges merely
to populate a screen. The fictional admin has no automatic management grant.

All 26 hosted checks passed: read-only metadata plus invalid-session probes in an
explicitly rolled-back writer transaction (row locks require write capability).
No application writes were committed or private data/key values printed. API5002
was restarted and live health 200, four unauthenticated write routes 401 and
PATCH/Idempotency-Key preflight passed. Actual authorized hosted writes/retries/
concurrency and resource UI remain separate work. No credential was changed.

Final local evidence: 151 Python tests, including 11 mutation/preflight tests;
494 contract checks; 265 isolated SQL checks, including 55 mutation cases. These
compare HMAC with a standard implementation and exercise private grants/key access,
school/ownership/eligibility rules, stale revisions, duplicate privacy, replay and
audit rollback with fictional in-memory records only. No frontend files changed;
prior seven client tests and both Vue builds were not repeated.
