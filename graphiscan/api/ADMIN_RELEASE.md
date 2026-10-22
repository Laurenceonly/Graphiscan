# Admin pilot release

## Scope

Publish the existing Vue admin on Vercel with the lightweight Flask v1 API on
Render Free, using the existing Supabase PostgreSQL, Auth and private Storage.
Expo/device checks and hosted model inference are separate work. The admin-only
API must explicitly use `GRAPHISCAN_REQUIRE_MODEL=false` and omit a model manifest.
It can read existing screenings, progress and protected images when Storage is
configured; it does not provide online inference in this deployment.

## Admin feature checkpoint

| Area | Source | Evidence / remaining verification |
| --- | --- | --- |
| Sign-in, password/privacy gates, logout | Connected to v1 session flows | Existing setup/catalog evidence; new-account gates still need role-client use. |
| Dashboard | Loaded-record counts, recent results, recorded activity | Earlier desktop/phone review; no fabricated global totals. |
| Add user | Temporary password, optional school, explicit role | Actual user-created Auth identity and matching profile confirmed. |
| Edit user | Current details, role/status, school memberships, permission scopes | Requires019 for detail projection and hardened updates; UI reviewed with fictional records. |
| Disable / activate | Confirmation, revision check, session invalidation | UI connected to existing PATCH; live action remains unverified. |
| Reset password | Issuer reauthentication, durable gate, one provider update, mandatory next password change | Requires019; provider mutation has not been exercised. |
| Delete account | Issuer reauthentication and DELETE confirmation; only unused accounts | Requires019. Self, last admin, sessions, assignments and history are protected; no live deletion performed. |
| Schools / students | Add/edit, school/grade/search, role-aware assignment choices | Existing v1 source; populated role behavior remains a pilot check. |
| Results / progress | Recorded results/history, details, authorized images and expert assignment | Existing v1 source; online inference excluded from this admin-only deployment. |
| Audit / settings | Scoped activity list, current-user password change | Existing v1 source; no synthetic activity presented as real. |

## Database rollout

Migrations017 and018 are installed and catalog-verified. Apply corrected
`db/postgres/019_admin_account_lifecycle.sql` once as the schema owner. The first
generated019 copy had damaged dollar quotes; the corrected complete file compiled
against an empty disposable PostgreSQL schema with001–018 and all five lifecycle
catalog flags passed. That compilation is not live reset/delete verification.

Then run the restricted read-only checker:

```powershell
python .\graphiscan\tools\check_v1_admin_writer.py --connect
```

It reports019 installation and checks the lifecycle function ownership/search
paths, exact reader/writer/private-helper grants, PUBLIC denial and private table
access. Do not repeat017 or018. Apply no account grants automatically.

## Provider operations and recovery

See `ADMIN_WRITES.md` for018 creation reservations. Migration019 adds
`admin_account_operations`: a committed target credential gate precedes the
single password-update or Auth-delete call. Old sessions lose access. Successful
reset clears that gate but requires a new password; successful deletion completes
only after Auth and the profile are absent. No plaintext credentials or hashes
are saved in operations or audit rows.

An uncertain operation is not replayed. The issuer can read only their own
operation status. Pending operations keep target access blocked and require a
private operator reconciliation of the operation, profile and provider outcome.
There is no public force-complete/unblock endpoint. Do not clear a gate or repeat
a provider write based solely on a timeout. Keep password/consent/history records;
use Disable for accounts that cannot be removed as unused.

## Deployment order

1. Complete019 rollout and restart the current local API; confirm routes come from
   current source, not an older process on5002.
2. Save reviewed source on `deploy/free-hosting` and update existing PR#1. Exclude
   `.env`, private uploads/model files, local tools, certificate/private export
   bundles and generated `output/`.
3. Sign in to Render. Create the **Free** Python web service from root `render.yaml`
   on the same branch, root directory `graphiscan`. Install
   `requirements-admin.txt`; use the Gunicorn command in the blueprint. Keep
   private configuration on Render. Local Windows certificate paths must be
   replaced by a host-accessible CA file or verified system trust while retaining
   `sslmode=verify-full`.
4. Set exact production Vercel origin in API CORS, and the actual HTTPS Render API
   origin in Vercel `VITE_HOSTED_API_ORIGIN`. Vercel builds
   `graphiscan/admin-web`, including its shared parent files, to `dist`.
5. Publish Vercel from the reviewed source and check hosted health/auth/access,
   pages and account actions with the appropriate authorized pilot accounts.
   Record what actually ran. Do not label the full system or mobile release done.

Render Free sleeps after idle periods; the sign-in client now allows90 seconds
for a cold start. Free service limits and provider eligibility still apply.
Never put server keys or database URIs in Vite/Expo public variables.

Sources: [Render free services](https://render.com/docs/free),
[Render environment and secret files](https://render.com/docs/configure-environment-variables),
[Render Python versions](https://render.com/docs/python-version),
[Supabase Auth user management](https://supabase.com/docs/guides/auth/managing-user-data).
