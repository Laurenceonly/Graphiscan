# First-login password change: user-run hosted success verified

Passing user-run hosted checkpoint (2026-10-20): supplied `password-check-passed`
with all **12** checks passing: two verified fictional sessions/forced-change gate,
actual v1 password endpoint, original/other-session and old-password denial, fresh
new-password bootstrap, preserved privacy gate and cleanup. A change was attempted
and application writes may have occurred; this was not a read-only check. No
credentials were saved/shared. No administrative Auth reset was reported. The
fixture's first-change gate is now cleared; do not rerun this forced-state checker
unchanged. This supersedes pending-hosted statements below and establishes the
standalone user-run success path, not generic deployed login/logout, refresh,
concurrency, failure recovery or client integration. Approved privacy wording is
the next input; latest local tests remain 103 Python, 465 contract and 123 SQL.

Latest hosted checkpoint (2026-10-20): user supplied
`writer-configuration-saved` with reader unchanged. Agent-executed
`tools/check_v1_password_writer.py --connect` passed all **23** checks using
verify-full and an explicitly read-only catalog transaction. Verified dedicated
writer login, UTC/bounded statement/lock settings, restricted role/no memberships,
no public schema CREATE, no direct public/Auth table or sequence grants, operation
RLS and both fixed-path definer functions with client/reader execution denied.
No mutation function was called and no application/Auth records changed. The
initial check exposed a missing effective lock timeout; the adapter now explicitly
sets session UTC/statement/lock settings and commits them before application work.
All 103 Python, 465 contract and 123 isolated SQL checks passed.

`POST /api/v1/me/password` accepts exactly `current_password`, `new_password`,
and `confirm_password`. An active issued account and valid current session are
required. Password/privacy onboarding gates are bypassed only for this operation.
Strength is the existing contract's eight characters, ASCII upper/lower/digit and
symbol; match/difference are checked without trimming. Each field is limited to
4096 characters and the JSON body to 16 KiB. Credentials never appear in responses,
audit rows, operation rows or exception text. Request-body logging must remain off.

## Sequence and failure behavior

1. Read the original token's trusted provider user/email, reauthenticate with the
   current password, verify the returned subject/session and locally sign out the
   extra verification session. Do not accept a client-supplied email/subject.
2. Commit `graphiscan_begin_password`: lock the profile, recheck active status and
   original provider session, revocations, expiry and security floor. Set pending,
   revoke current session IDs through the existing trigger, reserve one pending
   operation and audit in the same transaction. A racing attempt fails closed.
3. Update the original provider user password. Require HTTP 200 and matching ID.
   Send `current_password` as additional provider validation, but rely on step 1
   for current-credential verification independently of provider-version support.
4. Require confirmed provider global sign-out, then commit completion. Recheck the
   operation's subject and profile revision, clear pending/first-change, record
   password time/security version and audit atomically. The trigger also revokes
   sessions created during the pending interval. Return `success=true` and
   `next_action=sign_in`. Fresh sign-in is required after this response.

There are no automatic retries of credential/session writes. Unknown begin commit
outcome means no provider password write. Any error after begin leaves pending
closed, including definitive provider policy rejection, timeout, logout failure,
revision conflict or uncertain completion commit. First-change is cleared only
after confirmed provider success/logout. Pending denies even new sign-ins through
the existing access snapshot. Old sessions never become valid on recovery.

Supabase sign-out revokes refresh sessions but access JWTs may remain valid until
expiry; the API separately checks durable revocation and the session floor.
Sources reviewed 2026-10-20: [Auth REST API](https://github.com/supabase/auth/blob/master/openapi.yaml),
[password behavior](https://supabase.com/docs/guides/auth/passwords),
[session behavior](https://supabase.com/docs/guides/auth/sessions).

## Setup boundary

User reported successful SQL Editor execution of
`db/postgres/006_password_change.sql` on 2026-10-20 in the disposable project.
Do not rerun it. Hosted objects/grants have not been independently inspected.
It adds an RLS-protected operation table and a separate NOLOGIN server writer with
EXECUTE on only two fixed-search-path definer functions. It grants no direct table
or Auth access and makes no change to the existing read-only reader. Reviewed owner
execution is user-reported complete; separate private writer LOGIN/password setup is required before
setting `GRAPHISCAN_V1_PASSWORD_DATABASE_URL`. Use the dedicated writer's session
pooler URI, retain verify-full and the trusted CA. Do not use an owner/service role,
reader credentials or a client-exposed DSN. Startup makes no connection.

Without the writer setting the endpoint returns 503. Existing MySQL/Vue and Flask
page routes retain their current behavior; this v1 slice does not migrate them.

User subsequently reported successful separate writer LOGIN/password setup on
2026-10-20. Do not repeat it. Save the connection privately from the repository
root in a local interactive terminal:

```powershell
.\.venv\Scripts\python.exe .\graphiscan\tools\configure_v1_password_writer.py
```

Enter the newly saved **database writer** password at the hidden prompt. The
helper preserves the verified reader URI's host/pooler suffix/port/TLS query and
percent-encodes the new password. It saves only the separate writer setting in
the ignored `.env`, refuses to overwrite an existing writer value and prints
`writer-configuration-saved`. It makes no connection; actual writer login/grants
were subsequently verified by the agent's read-only preflight. The user reported
successful private helper execution; do not repeat configuration setup.

## Interactive fictional Auth password check

From the repository root:

```powershell
.\.venv\Scripts\python.exe .\graphiscan\tools\check_v1_password.py
```

This changes the fictional **Auth account** password and application first-change
flag and revokes its sessions. The first hidden prompt needs the existing fictional
Auth-account password used for the earlier passing Auth checker. The second and
third need a newly chosen, privately saved Auth-account password and confirmation.
Do not use database reader/writer passwords. No credentials are printed or saved;
the password policy is the existing eight-character upper/lower/digit/symbol rule.

The checker opens two verified fictional sessions, checks the forced-change gate,
calls the standalone Flask v1 endpoint, verifies both old sessions and old password
are denied, signs in with the new password, confirms bootstrap and privacy denial,
then cleans up its sessions. It refuses an already-changed fixture and does not
retry writes. Expected success is `password-check-passed`. Only share the JSON
status report, never passwords/tokens. A failure after an attempted change may
have left pending set or already completed the change; follow recovery below
instead of blindly rerunning. The user subsequently supplied all 12 passing
hosted checks on 2026-10-20. Recovery/refresh/concurrency are separate
checks; this is a standalone Flask test, not deployed client integration.

## Recovery for the disposable fictional account

Stop all API workers that could still finish the request. Establish that any
outstanding provider password request is finished before recovery; a local HTTP
timeout alone is not that evidence. Do not race recovery against the original
write or clear pending by hand. No timed automatic unlock exists.

As the schema owner, inspect only operation metadata for the fixed fictional
account. Do not share passwords, tokens, connection strings or private records:

```sql
SELECT o.operation_id, o.state, o.started_at,
       p.credential_update_pending,
       p.revision = o.profile_revision AS revision_unchanged
FROM public.password_change_operations o
JOIN public.user_profiles p USING (user_id)
JOIN auth.users u ON u.id = p.user_id
WHERE u.email = 'graphiscan.test@example.invalid'
ORDER BY o.started_at DESC;
```

If completed and not pending, the commit succeeded: require fresh sign-in, do not
repeat the password change. Otherwise authenticate with the intended **new**
password, never infer success from an error message. The fixture recovery tool
uses a hidden prompt, verifies the subject and fixed email, globally signs out,
and calls the same revision/operation-bound completion function:

```powershell
& '../.venv/Scripts/python.exe' tools/recover_v1_password.py
```

It accepts no CLI/piped credentials and requires explicit stopped-worker
acknowledgment. A failed new-password sign-in does not clear pending. If Auth never
changed the password, the owner must first use trusted Auth account recovery to
set the intended new password, keeping pending set; then run the tool. A changed
profile revision requires separate owner review; the tool refuses to overwrite it.
Do not casually update the captured revision to bypass that check. Failed or
malformed provider sign-in/cleanup can leave an extra provider session; owner
global-session cleanup is required before considering that failure resolved.

This tool is limited to the disposable fixture. Production recovery UI, delivery,
operator access and incident procedures remain release work. The writer can
complete operations only as a trusted server/operator capability; it is never
available to public Supabase client roles.

## Verification boundaries

Python HTTP/Flask/repository tests use mocks, including failure ordering and
recovery. PGlite runs actual migration/functions/grants/trigger/audit queries with
fictional Auth tables; it does not prove real concurrent transactions or hosted
provider semantics. Hosted password success, old-password denial, refresh/session
behavior, recovery, actual writer privileges and concurrency must be checked on
the fictional account before enabling clients. Privacy wording is still pending.
