# GraphiScan admin web

The hosted `/access` workspace now includes screening results and eligible expert assignment controls alongside the shared directory. It uses existing v1 reads, private image proxy and revision-checked assignment PATCH (migrations through014 are already applied here). Only admin/researcher accounts with `assignments.manage` see screening controls, and server school scope remains authoritative. The current Synthetic Test Admin has no automatic grant; the correct view may therefore be a permission message. No setup/migration repetition is required.

Results support status/grade filters and cursor pagination. Details preserve recorded screening type, historical model identity and human review authorship. Images use authenticated binary fetch and revocable local blob URLs. Assignment choices use the student's current school and actor-specific eligible expert pages. After a failed/conflicting save, reload details and inspect the current assignment before another submission. Writes are never automatically replayed. A refreshed permission loss clears displayed records.

Both Vue builds, shared-client tests and fictional intercepted Playwright checks passed, including narrow layout; populated hosted assignment/device testing remains pending. To rerun the synthetic browser fixture against local Vite5173, open a named Playwright CLI session and run `run-code --filename graphiscan/tools/check_hosted_admin_browser.js` from the repository root (create `output/playwright` first). Every API call is intercepted; fixture passwords and tokens are fictional and never sent to a provider. Browser screenshots are saved under `output/playwright/`. Legacy `/admin/*` routes continue using the existing MySQL API.

Hosted account onboarding is available at `/access`, linked from `/login`.
It uses the shared v1 login/refresh/password/privacy/logout flow; tokens remain in
memory and reload requires sign-in. Requires reviewed migrations through 008 for
durable sign-out. Admin/researcher accounts only. Student/result screens still
use the existing MySQL API; hosted credentials are never forwarded to those
routes. See [session integration](../api/SESSION_INTEGRATION.md) for setup/limits.

Vue 3 and Vite interface for administrators. Start the Flask backend from `graphiscan/`, then run `npm install` and `npm run dev` in this directory. Set `VITE_API_ORIGIN` in a local `.env` using `.env.example`. The app currently uses the MySQL backed Flask API; draft PostgreSQL schema files exist but have not been applied.

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
