Current handoff2026-10-22: migrations020/021 are applied and the last hosted
read-only preflight passed38 checks. PR#5 assignment API/admin and PR#6 shared
page/card styling are merged. Public bundle index-BMML1qyx.js contains the shared
cards, headers and centered Logout; public login returned200. Authenticated
assignment/permission/audit and reset/delete checks remain open. Expo integration
can begin against the deployed API; hosted inference is disabled, real-use privacy
publication is pending, and historical MySQL data/image transfer is incomplete.
No additional numbered migration is currently prepared. Do not rerun020/021.
# Assignment eligibility administration

Prepared2026-10-22. Source, isolated PostgreSQL and fictional browser checks pass.
Migrations020/021 are installed. The actual restricted hosted preflight passed
all38 checks, including guarded functions, exact runtime grants, PUBLIC denial,
table protection and writer connection settings. PR#5 published the matching
API/admin source. Authenticated hosted grant/revoke and scope/audit verification
remain open; the agent performed no real eligibility mutation.

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

1. The configured project already has020 and021. The latter removed leftover
   default TRUNCATE/REFERENCES/TRIGGER privileges. Do not rerun either migration.
2. From `graphiscan/`, run the current checkout's read-only check:

   ```powershell
   ..\.venv\Scripts\python.exe tools/check_v1_admin_writer.py --connect --require-assignment-access
   ```

   Require `admin-writer-setup-passed` and
   `assignment_access_migration_installed: true`. The new preflight also detects
   incomplete function sets, unexpected execution grants and direct table access.
   Existing private reader/admin-writer settings are reused; no new key is needed.
3. Matching API/admin source is published through PR#5. Check actual authenticated eligibility allow/remove, options and
   denied-scope behavior with a deliberately fictional account in an already
   authorized school. Source/preview evidence does not replace this hosted check.

Do not rerun017-019. Keep historical MySQL migration and real privacy publication
separate: the current notice remains limited to its existing fictional audience.
This work imports no records or images and does not publish privacy acceptances.

## Local evidence

-607 contract and507 isolated PostgreSQL checks passed, including35 assignment
  access cases and74 account-administration cases. SQL projections match OpenAPI.
-77 focused Python cases passed across assignment/admin/issuance/API/backend and
  hosted-app factory checks, including partial/missing020 rollout handling.
- Admin production build passed. Fictional Chromium at1440/390/320 exercised
  grant, revoke, school denial, single-dialog cancellation, unsaved-edit guards,
  lost-response reconciliation without replay and visible responsive footers.
  Nine intercepted saves were fictional; no real mutation occurred.

Authenticated mutation, distributed concurrency, real
role workflows, historical cutover, model hosting, Android/device and manuscript
evidence remain open in [CURRENT_REQUIREMENTS.md](../../CURRENT_REQUIREMENTS.md).
