Current publication checkpoint2026-10-22: PR#4 merged as b25d170; Researcher/Guest
role-choice removal is on main. Migrations020 and021 are applied; the last hosted
read-only preflight passed all38 checks. Assignment-access API/admin source is
being saved on feat/admin-assignment-access for a follow-up PR, not yet deployed.
607 contract/507 isolated SQL and77 focused Python checks plus admin build and
fictional responsive previews passed. Next: merge/deploy matching source, then
controlled authenticated hosted assignment checks. Earlier absent/pending SQL
and pause notes are historical; do not rerun migrations. Data/model/privacy/device/
manuscript and credential verification remain separate release gates.
# Assignment eligibility administration

Prepared2026-10-22. Source, isolated PostgreSQL and fictional browser checks pass.
Migration020 is installed: actual restricted catalog checks confirm all four
functions, guarded ownership/search paths, exact runtime grants and PUBLIC denial.
Readiness remains blocked by leftover TRUNCATE/REFERENCES/TRIGGER table privileges
for anon/authenticated/service_role. RLS is enabled. Migration021 removes those
privileges and awaits user application. The agent performed only read-only hosted
checks; no account or eligibility mutation occurred.

The Users editor provides **Manage assignment access** within Account actions.
Select a school and an assigning account, check the current state, then allow or
remove that account's ability to select this candidate. Existing student/result
assignments stay intact. The teacher/parent/expert assignment-option endpoint
uses these explicit links immediately on its next authorized request.

## Authority and prerequisites

The operator needs an active, onboarded admin/researcher session, global
`accounts.manage` and `assignments.manage` for the selected school. SQL repeats
those checks. A researcher may manage their own or teacher actors' eligibility;
only an administrator may manage a different administrator/researcher actor.

The candidate must be active. Teacher and expert candidates need school
membership. Administrative assigning accounts need their own current school
assignment-management grant. A teacher assigning account may select parents
only and must belong to that school. Eligibility can be provisioned before the
candidate's first-login gates are completed; it does not bypass those gates.
Verify the guardian relationship separately before linking a parent to a child.

No permission, role or membership is granted by this operation. Membership and
permission setup continue through the existing authorized account controls.
Accounts in an unfinished credential operation cannot have eligibility changed,
so its locked revision remains valid for credential reconciliation.

## API

`GET /api/v1/accounts/{candidate_id}/assignment-access` requires exactly one
`actor_id` UUID and `school_id` positive bigint string query parameter.

`PATCH` on the same path requires this JSON object:

```json
{
  "actor_id": "00000000-0000-4000-8000-000000000001",
  "school_id": "1",
  "expected_revision": 3,
  "eligible": true
}
```

Unknown fields, duplicate query parameters, invalid identifiers, nonboolean
choices and invalid revisions are rejected. The server generates the audit
request UUID. Bodies are bounded to8KiB. Both responses are no-store and contain
`data` plus `request_id`.

| Field | Meaning |
| --- | --- |
| `eligible` | A stored actor/candidate/school link exists, including a link made for a former role. |
| `effective` | The saved role link and all current role/status/membership/actor prerequisites permit selection. |
| `can_grant` | The current prerequisites permit establishing the link. |
| `revision` | Current candidate profile revision; changes to account details or another eligibility pair can make it stale. |

Revocation removes obsolete role links too, even after membership/status changes.
Granting replaces obsolete role links with the current valid role. A real change
advances the candidate revision and audits the actor/candidate/school in one
transaction. An unchanged choice adds no revision or duplicate audit. Audit
failure rolls the entire change back.

Profile locks serialize against existing assignment writers and scope changes.
The SQL checks cover atomic behavior in an isolated database; hosted concurrent
clients/revocation timing have not been exercised. After a timeout, conflict or
server failure, the dialog checks current access before allowing another save.
It does not blindly replay a write. Failed reconciliation can be closed after
the check attempt, with an operator notice and the stale account editor cleared.

## Rollout

1. The user has applied020. Apply only
   [021_assignment_table_privileges.sql](../db/postgres/021_assignment_table_privileges.sql)
   using the reviewed schema owner in SQL Editor. It revokes leftover default
   TRUNCATE/REFERENCES/TRIGGER privileges without changing records or functions.
   Do not rerun020.
2. From `graphiscan/`, run the current checkout's read-only check:

   ```powershell
   ..\.venv\Scripts\python.exe tools/check_v1_admin_writer.py --connect --require-assignment-access
   ```

   Require `admin-writer-setup-passed` and
   `assignment_access_migration_installed: true`. The new preflight also detects
   incomplete function sets, unexpected execution grants and direct table access.
   Existing private reader/admin-writer settings are reused; no new key is needed.
3. Publish the matching API and admin source through the normal main-branch
   deployment. Check actual authenticated eligibility allow/remove, options and
   denied-scope behavior with a deliberately fictional account in an already
   authorized school. Source/preview evidence does not replace this hosted check.

Do not rerun017-019. Keep historical MySQL migration and real privacy publication
separate: the current notice remains limited to its existing fictional audience.
This work imports no records or images and does not publish privacy acceptances.

## Local evidence

-607 contract and506 isolated PostgreSQL checks pass, including35 assignment
  access cases and73 account-administration cases. SQL projections match OpenAPI.
-77 focused Python cases passed across assignment/admin/issuance/API/backend and
  hosted-app factory checks, including partial/missing020 rollout handling.
- Admin production build passed. Fictional Chromium at1440/390/320 exercised
  grant, revoke, school denial, single-dialog cancellation, unsaved-edit guards,
  lost-response reconciliation without replay and visible responsive footers.
  Nine intercepted saves were fictional; no real mutation occurred.

Hosted021 application/full preflight, authenticated mutation, distributed concurrency, real
role workflows, historical cutover, model hosting, Android/device and manuscript
evidence remain open in [CURRENT_REQUIREMENTS.md](../../CURRENT_REQUIREMENTS.md).
