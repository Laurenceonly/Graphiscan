# GraphiScan admin web

Publication2026-10-24: the palette source is committed/pushed and PR#11 is
confirmed merged. Vercel preview for d07cabe was READY and user reports viewing
the admin. Production build passed1834 modules. Full authenticated admin/role
checks and exact later production deployment state remain separate evidence.

Local palette update2026-10-24: user requested matching Expo colors, including
login, without layout changes. Shared palette now uses blue #095df1, hover
#074bc2, paper #f7faff, ink #14263c and muted #5c6c81 with matching border and
selection tints. Login and hosted workspace inherit those roles. Production
build passed; browser review/publication remain separate. Expo code is unchanged.

Prepared assignment setup2026-10-22: Edit > Manage assignment access uses the new
scoped GET/PATCH account eligibility API. It needs020 installed before publication;
actual metadata still shows019 as latest. Source/build and fictional1440/390/320
grant/revoke/recovery previews pass. See [rollout and prerequisites](../api/ASSIGNMENT_ACCESS.md).

Current published checkpoint (2026-10-22): admin is live at
https://graphiscan-admin.vercel.app/login and uses the Render Free API. User
confirmed hosted login/dashboard; PR#1 merged and Render follows main. Migrations
through019 are installed, account actions are implemented, and no repeated SQL
setup is needed. Full hosted action/assignment/role verification remains open;
model inference is disabled on this API. See `../../CURRENT_REQUIREMENTS.md`.
Older preparation-only and pending017 statements below are historical.

Latest hosting checkpoint (2026-10-22): Vercel admin project/GitHub connection is prepared; no live deployment. The API host must satisfy the user's free model-hosting requirement. See [`HOSTING.md`](../api/HOSTING.md). Schema migrations through017 and the separate admin writer are installed and verified read-only. Older setup-pending statements below are historical. The preparation branch `deploy/free-hosting` has automatic Vercel deployments disabled until a valid public API origin is configured.

Verified setup (2026-10-21): user applied [`016_admin_reads_setup.sql`](../db/postgres/016_admin_reads_setup.sql); all14 independent restricted read-only hosted checks passed. The guarded function, indexes and fictional-admin global `accounts.manage`/`audit.read` grants are installed. **Do not repeat016 or the grant setup.** The current-source hosted API5002 is running; health200 and anonymous new list routes401. Previous sessions were revoked by permission changes, so sign in fresh. Populated UI list confirmation remains pending. For a new disposable project after015, run only that atomic bundle once, not canonical016 separately; it deliberately refuses a different identity or absent workflow-test audience. The bundle/checker queries passed146 isolated SQL checks.

Account updates are implemented in source but not enabled on the hosted project. Review [`ADMIN_WRITES.md`](../api/ADMIN_WRITES.md) and apply migration017 only after review; 016 must not be rerun. Account creation and temporary-password reset remain open.

Design reference: the supplied dashboard screenshots guide the hosted visual layout, while the original admin pages guide navigation and actions. The hosted shell now has a white sidebar, pale blue active item, neutral content surface and a slim breadcrumb header. The brand underline and top-right profile display were removed at the user's request. Inter is shared with login: page headings28px/600, section headings16px/600, labels/actions14px,48px filter controls and44px standard actions. Red logout and semantic status colors remain. Students/Schools use existing tables/native modal editors; Progress reads existing scoped history and Settings changes the current password. Users/Audit lists use installed016 and separate global permissions; account mutations remain pending.

The main admin sign-in is `/login`. Root `/` and the former `/access` address resolve to this same hosted admin page. It accepts issued admin/researcher accounts through `/api/v1`; teacher/expert/parent accounts use the separate user app. There is no switch between authentication systems on the main sign-in. The old MySQL admin interface remains separately available at `/legacy-login` and `/admin/*` until hosted feature parity is complete. Legacy guards, logout, password changes, API401 handling and the older Flask login redirect return to `/legacy-login`; they do not establish hosted sessions. Existing legacy browser tokens never redirect the main hosted sign-in. No credentials or sessions are shared between the two systems.

After successful sign-in and onboarding, `/workspace` opens Dashboard. Its original eight choices remain: Dashboard; Users/Students; Results/Progress; Audit Logs/Settings; Logout. Schools remains within Students. Counts describe currently loaded filtered records, not global totals. The activity chart shows seven calendar dates ending at the newest loaded dated screening and appears only when at least two dates have records; it does not measure clinical progress. At desktop, chart/review and recent/breakdown panels share rows; phones use one column. Duplicate descriptions, shortcut buttons, profile cards and filler summary boxes were removed. Users/Audit calls now return200 in live signed-in requests, and SQL metadata/grants were independently checked; displayed private rows were not inspected. The router preserves memory-only tokens and sign-out returns to `/login`; reloading requires sign-in. The legacy `/admin/*` session remains separate.

Run `run-code --filename graphiscan/tools/check_hosted_dashboard_browser.js` for synthetic dashboard/navigation/modal checks. `check_hosted_navigation_browser.js` checks matching login/page fonts, exact heading alignment across six widths, list/history pagination and Settings password behavior. `check_hosted_login_layout_browser.js` checks nine login sizes without signing in. The other browser fixtures intercept every API call. Login fills the whole tab with an edge-to-edge42/58 white/blue split,440px form,54px inputs and a complete CSS laptop showing the current synthetic-dashboard capture. The right headline stays on one line; Welcome back, its subtitle and privacy note are centered while field labels remain left-aligned. Tablets collapse to one column. No fake records or requests are installed in the app.

The hosted admin page includes screening results and eligible expert assignment controls alongside the shared directory. It uses existing v1 reads, private image proxy and revision-checked assignment PATCH. Only admin/researcher accounts with `assignments.manage` see screening controls, and server school scope remains authoritative. Migrations through016 are applied in the current test setup; the synthetic admin retains a bounded school assignment grant plus global account/audit read grants. No setup/migration repetition is required.

Results support status/grade filters and cursor pagination. Details preserve recorded screening type, historical model identity and human review authorship. Images use authenticated binary fetch and revocable local blob URLs. Assignment choices use the student's current school and actor-specific eligible expert pages. After a failed/conflicting save, reload details and inspect the current assignment before another submission. Writes are never automatically replayed. A refreshed permission loss clears displayed records.

Both Vue builds, shared-client tests and fictional intercepted Playwright checks passed, including narrow layout; populated hosted assignment/device testing remains pending. To rerun the synthetic browser fixture against local Vite5173, open a named Playwright CLI session and run `run-code --filename graphiscan/tools/check_hosted_admin_browser.js` from the repository root (create `output/playwright` first). Every API call is intercepted; fixture passwords and tokens are fictional and never sent to a provider. Browser screenshots are saved under `output/playwright/`. Legacy `/admin/*` routes continue using the existing MySQL API.

Hosted account onboarding is available at `/login`; `/access` redirects there.
It uses the shared v1 login/refresh/password/privacy/logout flow; tokens remain in
memory and reload requires sign-in. Requires reviewed migrations through 008 for
durable sign-out. Admin/researcher accounts only. Hosted records use v1; legacy
`/admin/*` screens use the existing MySQL API. Hosted credentials are never
forwarded to legacy routes. See [session integration](../api/SESSION_INTEGRATION.md)
for setup history and limits.

Vue 3 and Vite interface for administrators. Run `npm install` and `npm run dev` in this directory. The hosted setup uses the configured `VITE_HOSTED_API_ORIGIN`; legacy pages use `VITE_API_ORIGIN` and the MySQL-backed Flask app. Safe public-origin examples are in `.env.example`. See the current checkpoint in root `RESUME.md` before starting services or repeating setup.

With MySQL running, run the read-only API baseline from the repository root:

```powershell
& '.venv\Scripts\python.exe' graphiscan/tools/check_local_api.py
```

It checks API responses using existing active account IDs and temporary tokens
inside the test process. It does not change database records or print response
records. Roles without active accounts are reported as skipped. This does not
test real login, browser rendering, account actions, or password changes.

Admin API requests recheck the account's current role and status. Deleted,
inactive, or demoted admin accounts lose access through previously issued
tokens; sessions still use the current process-local token store until the
Supabase Auth migration.

For isolated admin write verification, start a second frontend in a separate
PowerShell window from this directory:

```powershell
$env:VITE_API_ORIGIN='http://127.0.0.1:5001'
npm.cmd run dev -- --host 127.0.0.1 --port 5175 --strictPort
```

Then run from the repository root with MySQL running:

```powershell
& '.venv\Scripts\python.exe' graphiscan/tools/check_admin_writes.py
```

Add `--phone` to exercise the same write workflows at a 390px browser viewport.

This copies current table definitions into a uniquely named temporary database,
seeds fictional accounts, and runs API and actual-browser write checks. It needs
database creation/deletion permission, free API port 5001, and Playwright CLI
through `npx`. The normal API and its configuration stay unchanged. The browser
uses only the isolated API; fixture passwords in the test scripts are synthetic.
The runner closes its test browser/server and drops only the database it created,
then compares the original database's schema/content fingerprints. Avoid other
record edits during the run so concurrent activity does not invalidate that
comparison. An interrupted process may require cleanup of its temporary database.

The current modal directive in `src/directives/dialog.js` provides dialog naming,
focus entry/containment/return, Escape handling through each existing close
handler, background inertness, and scroll locking. Login, settings, filters, and
record forms now have explicit field names; errors and loading/success messages
use alert/status roles. These semantics were checked in Chromium with synthetic
data at 320px, 390px, and 1440px. Slow/failing/offline responses and failed-save
retry were simulated; the 390px writes also ran against a disposable real MySQL
database. This is not a screen-reader certification or physical-phone test.
