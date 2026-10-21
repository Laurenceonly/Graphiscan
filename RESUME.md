# GraphiScan resume checkpoint

## User stopped for later; resume at teacher onboarding, 2026-10-20

User requested “lets continue later save progress”. Work stopped after saving this checkpoint. Overall roughly56%, not measured production readiness.

Completed: user created3 fictional Auth accounts; user applied atomic015; all23 agent restricted read-only setup checks passed. Updated hosted API5002(session43462) health200. User confirmed admin fresh sign-in/newnotice acceptance/synthetic school+student; API logs support login/me/notice/acceptance/schools/students/screenings HTTP200, content/visual confirmation user-reported. Earlier162 v1 Python/114 isolated actual-bundle SQL tests passed.

NEXT when user resumes: open http://localhost:5174 (HOSTED Expo, session77508), sign in as graphiscan.teacher.test@example.invalid with privately saved TEMP password; choose/save private new password, sign in again, explicitly accept graphiscan-workflow-test-v1, open Students and confirm Synthetic Workflow Student. This teacher onboarding is NOT yet reported done. Then onboard expert and parent individually, followed by synthetic teacher upload→admin expert assignment→expert review→parent release/withdrawal and stored Follow-up checks. Keep admin http://127.0.0.1:5173/access available; admin account uses its existing current password and already accepted new notice.

Services were intentionally left as-is; availability after a break is NOT guaranteed. Verify liveness before restarting anything: hosted API5002, Vue admin5173, Expo http://localhost:5174 (NOT numeric127.0.0.1 for this Expo binding). Expo was launched explicit EXPO_PUBLIC_API_MODE=hosted, EXPO_PUBLIC_HOSTED_API_ORIGIN=http://127.0.0.1:5002, CI/offline/BROWSER=none, --web --port5174 --localhost. CI disables auto reload. Hosted login rendered in clean browser without credentials; CORS5174 allowed. Legacy API5000 was previously restored, irrelevant to hosted work. Do not restart live services unnecessarily or infer passwords from config.

DO NOT repeat migrations001–015, model publication/Storage setup, Auth creation, old seeds, or original first-change/privacy checkers. Do not reset admin/passwords or seed acceptance. No secrets saved in checkpoint. New-role onboarding, populated hosted uploads/reviews/parent release, native/device/deployment/three-class work remain unverified. XAMPP repair STOPPED by user direction; legacy data has verified offline file copy but accounts/students NOT deleted. Do not resume repair/deletion merely to clear old data.

## Admin onboarding confirmed; hosted Expo web ready, 2026-10-20

Supporting API43462 logs show login/me/notice/acceptance and schools/students/screenings HTTP200 at22:22. Content/visual confirmation remains user-reported; no agent credentials used.

User said “yes done” to admin fresh sign-in/newnotice acceptance/synthetic school+student check. Record as user-reported success, not independent full admin browser/write verification. Started mobile-app Expo in HOSTED mode, public API origin http://127.0.0.1:5002, web port5174, --localhost, CI/offline/BROWSER=none; session77508 active. IMPORTANT browser address is http://localhost:5174 (numeric127.0.0.1:5174 refused because localhost binding). Root HTTP200; bundle605modules compiled; clean Playwright snapshot showed actual hosted “issued teacher, expert or parent” login/fields, no blocking console error. No credentials entered or role changes. CORS preflight for5174 allowed. DevTools installer fell back after sandbox write denial, app nevertheless compiled/rendered; no need to fix it. CI means no automatic source reload; restart only if code changes.

NEXT USER ACTION: at http://localhost:5174 sign in as graphiscan.teacher.test@example.invalid with privately saved TEMP password; change to privately saved new password, sign in again, explicitly accept new notice, open Students and confirm Synthetic Workflow Student. Never ask passwords in chat. Teacher first; expert/parent next. Keep admin5173 open for later expert assignment. No real hosted upload/review/release/device test yet. Overall56%. No SQL/setup/checker repeat or XAMPP work.

## Atomic015 verified; updated hosted API active, 2026-10-20

User reported015_workflow_fixtures.sql SUCCESS. DO NOT repeat bundle/source/prior migrations or recreate/reset Auth accounts. Agent ran `tools/check_v1_workflow_setup.py --connect`: all23 checks passed, restricted TLS/read-only/bounded connection, audience column,4 active role profiles,exact new4-ID notice/hash/metadata,old notice retained,narrow admin grant,2 memberships and three functions' scope/ACLs. No application writes. Preflight does not test populated student/eligibility APIs or role workflow.

Verified exact5002 listener process command, stopped ONLY that listener and started updated hosted API; session43462 active. /api/v1/health200, admin5173/access200, anonymous screenings+notice401. No other services stopped, no SQL/credential/XAMPP/legacy-deletion changes. Overall56%.

NEXT USER ACTION: fresh sign-in at http://127.0.0.1:5173/access with existing Synthetic Test Admin/current password; grant normally invalidated old sessions. Read/explicitly accept graphiscan-workflow-test-v1, then confirm synthetic school/student. NO admin password reset. After user confirms: start/verify mobile-app Expo in HOSTED mode (public origin5002; web port5174 aligns existing CORS), onboard teacher/expert/parent individually with private temporary→new passwords and new notice. Do not reuse old MySQL sign-in or old forced-change checker. No populated hosted upload/review/parent/client/device/deployment evidence yet. Keep XAMPP repair stopped; legacy accounts archived, not deleted. Following apply015 instructions are historical/superseded.

## User created3 Auth users; atomic015 ready, 2026-10-20

NEXT USER STEP: paste ENTIRE `graphiscan/db/postgres/015_workflow_fixtures.sql` into a NEW Supabase SQL Editor query and run ONCE. Bundle prepared/tested, NOT APPLIED. Do NOT run015_privacy_test_audience.sql or seed_workflow_fixtures.sql separately or repeat001–014. Source seed contains builder placeholder; only generated bundle is executable handoff. No XAMPP work needed.

User reports exact teacher/expert/parent Auth accounts created; passwords private. Bundle adds bounded1–16-ID notice audience to bootstrap, notice-read, acceptance, directory AND screening direct gate while preserving old singleton/ordinary behavior/ACLs. Creates3 active forced-first-change profiles,1 fictional school/student,ONLY admin school-scoped assignments.manage,2 memberships/4 eligibility links and new notice for exact4 IDs. Preserves admin password and old notice text/audience/acceptances; retires old current flag, seeds no acceptances. Missing/unconfirmed/banned/deleted/conflicting state aborts all DDL/data; repeat refuses without overwrite. No hosted/Auth/model/screening/image/delete writes or restart yet.

Verified162 v1 Python tests +114 isolated PGlite actual-bundle assertions including rollback/scope/compatibility/session invalidation/ACLs and restricted-reader verifier query. Read-only `tools/check_v1_workflow_setup.py --connect` prepared/compiled, not hosted-run. AFTER user-reported SQL success: run this checker, then restart ONLY hosted5002 after verifying exact live process. Existing admin grant invalidates old sessions: fresh sign-in/new notice acceptance needed, NO admin password reset. Then connect hosted Expo and individually onboard newroles without rerunning old forced-change fixture checker. Overall55%; populated upload/review/parent/device/deployment unverified. Legacy repair remains stopped, records archived not deleted.

## Stop XAMPP repair; prioritize hosted accounts, 2026-10-20

Latest user steering: asks whether XAMPP is still needed and explicitly wants no tokens spent fixing it if unnecessary. Hosted Supabase/API5002/Vue admin/Expo workflow does NOT require XAMPP or legacy MySQL. STOP MySQL repair work and continue selected fictional hosted admin/teacher/expert/parent setup. Legacy demo-account deletion remains authorized but unperformed; do not spend further repair effort to achieve it absent new user request. Preserve archived legacy data for now; no claim of deletion.

Diagnosis before stop: console startup identified fatal “Incorrect file format 'global_priv'” in MariaDB's internal privilege table. Offline copy verified all172 files/111410390bytes at ignored `.local-backups/mysql-offline-20261020T123327Z-56badc`; manifest explicitly says database_restore_verified false (file preservation only). Disposable copied global_priv check/recover/check all exited1, classified not-Aria; ORIGINAL privilege/application files never repaired/replaced/deleted. No backup reset or credentials changed. Added `tools/backup_mysql_offline.py`. Last foreground mysqld attempt exited1; no new running MySQL process started afterward. Hosted APIs were restored earlier(session83381 port5002,23855 port5000), admin Vite5173 remains. Overall53%. Next implement/test bounded notice audience+guarded selected fictional fixtures, then user manually creates3 Auth accounts with private temporary passwords; do not unrestrict old notice or seed acceptances.

## Stopped APIs restored; MySQL accepts TCP but sends no greeting, 2026-10-20

User reported loading tab/XAMPP restart log. Admin Vite5173 HTTP200, APIs5000/5002 were offline; Vue user5174 unavailable. Restored both Flask APIs with debug/reloader OFF, sessions83381(hosted5002),23855(legacy5000), both /api/v1/health HTTP200. No setup/SQL repeat or credential change. Hosted /access may now be retried; actual authenticated browser success not checked. User was asked which tab URL; no answer yet.

MySQL after user's restart still returns2013 to read-only inventory. Credential-free raw TCP check on configured loopback/default port connects but no4-byte greeting within4sec. Running XAMPP indicator is not usable SQL evidence. No backup/deletion/database-file repair occurred. Deletion of identified OLD LEGACY DEMO accounts remains authorized, preserving hosted admin/new setup/models/audit evidence; need usable SQL+verified backup+exact dependencies before execution. New fictional teacher/expert/parent Auth/profile/notice/audience setup remains not implemented. Overall53%.

## User selected fictional fixtures and authorized old legacy demo account removal, 2026-10-20

Latest steering: use proposed admin-through-parent fictional accounts; user then said “yes okayy dewlete old acc” after recommendation to delete old LEGACY DEMO accounts/synthetic students after backup, preserving current HOSTED Synthetic Test Admin/new hosted setup/model/audit evidence. Treat identified legacy demo-account deletion as authorized; do not ask permission again for that scope. Do not delete uncertain/real records, hosted fixtures or models. No new fictional Auth users, role profiles, notice/audience migration or fixture SQL have been created/applied yet; the draft package remains proposed implementation.

Cleanup attempted: new `tools/inspect_legacy_retirement.py` is count-only/read-only. Elevated actual run initially MySQL2003. Started C:/xampp/mysql/bin/mysqld.exe with existing my.ini and --standalone, hidden process20348. Two read-only retries returned2013; elevated logs show crash recovery/startup and port3306 listening, but usable SQL connection is unverified. NO inventory rows obtained, backup, deletion, database-file repair, hosted writes or API restart. Need usable MySQL, then verified backup and exact demo/dependency inventory before authorized deletion. XAMPP MySQL now relevant only to legacy cleanup; Apache unnecessary. Overall53%. Earlier awaiting-fixture-choice note is superseded; do not treat selected fictional setup as authorization to unrestrict old admin-only notice.

## Fictional role-flow review package prepared, awaiting fixture choice, 2026-10-20

User said next. Prepared `graphiscan/api/FICTIONAL_WORKFLOW_SETUP.md` and separate `fictional-workflow-notice.draft.txt`. Proposed exact3 fictional teacher/expert/parent Auth emails, one synthetic school/student, explicit memberships/eligibilities and ONLY school-scoped assignments.manage for existing Synthetic Test Admin. No global/admin-account/permission/school-management grants. Asked asynchronously whether to prepare fictional setup or use existing issued accounts; no answer recorded yet. Do not treat silence as approval of accounts/grants/notice.

Source constraint found: one current notice globally plus single test_subject_id. Proposed bounded multi-account audience extension still needs implementation/tests/review; no migration or fixture SQL is prepared or applied. New notice would require explicit acceptance by all4 roles, including admin, and retire old current flag while preserving original text/audience/acceptances. Never clear old audience or seed acceptance to bypass. Draft language reviewed against binary predictor/current parent Validated gates; no new runtime/hosted role evidence. Overall stays53%. Next: incorporate user's fixture choice, implement/check exact scoped package and obtain review before owner application. Prior admin UI work is complete; do not repeat builds or hosted setup absent changes.

## Hosted Vue admin screening and assignment UI connected, 2026-10-20

Implemented admin `/access` screening list/detail/status+grade filters, private blob image, recorded model/report/review fields and current-school eligible expert selector with pagination. HostedScreenings mounts through shared HostedAccess scoped slot; existing Vue/MySQL routes and user workspace preserved. PATCH uses screening revision; failed/uncertain/conflicting writes require detail reload, no replay. Permission refresh clears records. Both Vue production builds and17 shared-client tests passed; fictional intercepted Chromium checks passed for assignment, conflict recovery, private image, pagination, permission loss, signout and390px layout. No real hosted assignment writes, accounts/grants/notices/migrations or API restart. Local admin Vite5173 was started; API5002 untouched. XAMPP is unnecessary for hosted work; only legacy MySQL flows need it.

Rough overall53%. Next dependent work is issued teacher/expert/parent profiles with appropriate reviewed notice and explicit school/eligibility links, followed by populated hosted upload/review/parent-release verification. Existing Synthetic Test Admin remains without automatic management grants and current notice remains admin-only. Do not broaden notice/grant roles merely to populate screens. Native/device, production and three-class work remain open. Earlier hosted-admin-placeholder instructions below are superseded.

## Catalogue and synthetic private Storage I/O verified, 2026-10-20

User provided all12 passing model-catalogue-check results: hosted3 version metadata/accuracies, unique selectable MobileNetV2 default, anonymous denial and temporary Auth-session cleanup. Agent added/ran tools/check_v1_storage_io.py --apply; all5 passed (configured, syntheticPNG put, byte-exact authorized get, public-route denied, delete+confirmed404). Only generated whitePNG used; no screening/database writes. Temporary ignored model/storage-check.local receipt was removed after confirmed cleanup. Credentials never printed. No rerun/restart needed; current API40531.

Rough overall51%. Next coding task can proceed without accounts: hosted admin screening list/detail and current eligible expert assignment controls, replacing the hosted shared workspace's later-update placeholder. Existing admin is Vue, user app Expo; preserve legacy interfaces. Current only issued fixture/notice is Synthetic Test Admin, no automatic manager grants or student access. Populated teacher→expert→parent testing still requires specifically issued role profiles, school/eligibility links and a separately reviewed appropriate notice (do not broaden old admin-only notice). Native/device, production and three-class work open. Earlier publication/check/Storage-not-verified notes superseded.

## Publication reported, API active, interactive catalogue check next, 2026-10-20

User reported publish_binary_models.sql success. Restarted only verified API5002 processes; session40531 active, schema-v2 runtime/all3 model artifacts/Storage factory configuration independently confirmed. tools/check_v1_model_catalogue.py compiled successfully. NEXT USER COMMAND from root: .\.venv\Scripts\python.exe .\graphiscan\tools\check_v1_model_catalogue.py . It prompts for CURRENT fictional Auth password privately (not database writer/S3 password), signs in fixed fictional admin, checks running API versions/evaluation accuracies/default/anonymous denial and revokes its temporary session. No screening/password/notice changes; Auth/session binding writes occur. Protected catalogue publication is user-reported only until checker output; do not claim verified or repeat SQL/restart. Overall49%. Earlier publication/restart instructions below are superseded.

## Three hosted model versions staged, publication next, 2026-10-20

User authorized integration. Implemented v1_models.py schema-v2 runtime with3 fixed supported architectures, exact hash/version/rule/preprocessing and source/class-map pins, separate cached networks and serialized inference. Legacy model/path/globals unchanged. v1_backend accepts schema-v2 or old single-model manifests; v1_uploads resolves explicit/default catalogue choice to installed identity before existing atomic reservation. Completed retries survive missing/withdrawn catalogue entry. Existing React hosted selector already consumes these metadata flags.

Ran tools/prepare_v1_model_catalogue.py successfully: all3 ignored hash-named weights staged under model/versions; model/deployment.local.json saved and server .env manifest path configured. Prepared UNAPPLIED graphiscan/db/postgres/publish_binary_models.sql, image-level measured evaluation and3 versions/defaultMobileNetV2, no account/grant/student writes. Existing conflicting default/identity/withdrawal aborts transaction; exact repeat-safe. Next user action: run ONLY this publication SQL in a new Supabase query. Do not rerun migrations or old prepare_v1_model_manifest.py (would conflict with new manifest). API5002 session32790 still predates saved Storage/manifest; restart after publication, then authenticated metadata/uploads. No automatic deployment/cutover.

Verification:160 v1 tests passed before final2 upload cases; expanded upload suite18 passed;11 isolated PGlite publication assertions passed using actual001–003 schema (metadata/default/repeat/conflict rollback/withdrawal); actual VersionedBinaryRuntime loaded and inferred synthetic whitePNG on all3 model artifacts (session89226 exited0). No Storage writes/real user images/database writes in smoke. Docs api/MODEL_EVIDENCE.md and SCREENING_WRITES.md current. Rough overall49%; populated role/privacy/upload/review/release, native/device, production and planned three-class work remain pending.

## Model evidence found and locally reevaluated, 2026-10-20

Owner path graphiscan/training_results exists. Active model exactly matches saved ResNet50 (SHA2569c6e2cd5b031a0ec07378d73089286ba1140707b5861652b7152c48d2bf20fbd). Historical CSV86.03% is at training0.50 threshold/TensorFlow resizing, not current0.75/PIL path. Added and ran tools/evaluate_v1_models.py --compare: all136 existing test images completed on all3 recorded binary artifacts. At0.75 MobileNetV2 leads85.2941%accuracy, ResNet50 and EfficientNetB0 each72.7941%. Full metrics/matrices/hash evidence: api/MODEL_EVIDENCE.md plus ignored training_results/hosted_runtime_evaluation.local.json. No exact-content split intersections; counts627train/134validation/136test; writer separation unverified. No weights/threshold/manifest/default/registry/database changed. Next code: versioned pinned multi-artifact runtime/evaluation publication so best supported model and selector reflect new comparable evidence; existing adapter only supports active ResNet50. Do not publish historical86.03% as hosted accuracy. User no longer needs to locate results. Three-class work remains separate. Evaluation process33755 exited0. Rough overall47%.

## Storage credentials saved and read access verified, 2026-10-20

User completed configure_v1_storage.py. Real S3 HeadBucket and bounded MaxKeys=1 screenings-prefix listing passed using the configured adapter; no writes or secret/object-name output. Privacy, put/get/delete and full upload remain unverified. Confirm Public bucket OFF; do not repeat credential setup. Model evaluation location remains needed (filename search found no matching evaluation/metrics/report artifacts); no manifest/publication fabricated. API session32790 predates saved Storage settings, so restart after remaining configuration. Rough overall46%; earlier absent-Storage instructions superseded.

## Atomic 013+014 verified and local API activated, 2026-10-20

User reported the single bundle applied. All 19 tools/check_v1_screening_writes.py --connect checks passed: read-only bounded restricted connection, capability grants, no reader/writer upload-job table grants and three nonexistent-identity denials. No mutation functions invoked. Only verified API5002 processes were stopped; updated API session32790 now has health200 and six new protected route probes401/no-store. Do not repeat migrations or restart unnecessarily. Presence-only configuration check confirms all five Storage settings and GRAPHISCAN_V1_MODEL_MANIFEST absent. Next user action: create a private Storage bucket, copy same-project S3 endpoint/region and server-only generated S3 credentials into tools/configure_v1_storage.py hidden prompts locally. Never request keys in chat. Model evaluation path remains unanswered; no invented publication metadata. Issued user roles/privacy, admin assignment integration, populated hosted writes, device checks and deployment remain pending. Rough overall45%; prior unapplied-bundle instructions below are historical.

## Hosted writes prepared, awaiting ONE atomic bundle, 2026-10-20

Locally implemented review/eligible expert assignment, official upload reservation/completion, model catalogue, request-state recovery, private image proxy and cleanup. React hosted upload/review/image controls are connected, no MySQL fallback. **Next user step: apply only graphiscan/db/postgres/013_014_screening_writes.sql once in Supabase SQL Editor. Do NOT run 013_screening_writes.sql or 014_screening_uploads.sql separately as well.** The bundle wraps both in one transaction and is tested directly, with drift checks. No new DB credentials or seeded records/grants/models/buckets. After reported success, run tools/check_v1_screening_writes.py --connect (read-only catalogue/denials), then restart the API. Current old API5002 session54308 has not been restarted early.

Tests: 155 v1 regressions passed (included initial14 new tests), expanded new suite16 then passed; 17 shared JS/11 mobile, TypeScript, 494 contract, 31 write/38 upload/45 read +284 earlier SQL checks, Expo web/Android JS exports and both Vue builds passed. No real S3/model inference/upload or hosted write/device/deployment. Live concurrency remains unverified despite SQL locking/unique invariant and competing-reservation tests. S3 SDK installed/pinned, Expo crypto installed. Pending mobile actions are memory-only.

Private bucket/S3 credentials, pinned artifact manifest and reviewed evaluation/registry publication remain required; runtime fails closed without them. Storage setup CLI hides inputs and refuses non-TTY use; never ask for secrets in chat. prepare_v1_model_manifest.py hashes existing artifacts but does not verify/publish evaluations. User was asked asynchronously for evaluation file/folder path, no answer yet; do not invent metadata. Current fictional account/temporary notice is still admin-only; issued user roles/appropriate reviewed notice remain pending. Admin hosted assignment UI still needs integration. See graphiscan/api/SCREENING_WRITES.md. Rough overall45%; older pending-work instructions below superseded by this slice.

## Migration 012 verified and API activated, 2026-10-20

User reported 012 success. Agent ran tools/check_v1_screening_reads.py --connect: all 22 hosted bounded TLS/read-only metadata/privilege/zero-identity checks passed, no application writes/private output. Restarted only verified app.run/port5002 Python processes; current API session54308 is active. Health200; four unauthenticated screening list/detail/history/report routes401/no-store. No repeat SQL/password/seeding/refresh request is needed. Authenticated populated reads, issued-role notice/accounts, hosted writes and React/native checks remain pending; no cutover/deployment claimed. Overall estimate41%. Following apply-012/restart instructions are superseded.

## Active hosted screening read slice, 2026-10-20

Implemented ScreeningReadService, four guarded v1 read routes and **unapplied 012_screening_reads.sql**, granting only a single function to the existing reader. Scope/gates repeat in SQL; parent current Validated release filtering precedes pagination. Added React EXPO_PUBLIC_API_MODE=hosted Auth/password/privacy and directory/results/history/report flow reusing the shared client; legacy stays default until hosted writes exist. No legacy/Supabase token or UUID bridge. The only hosted fixture is still an admin and its test notice is admin-only; do not bypass user-role/notice setup to test React. Seven prior count/read tests are separate from this v1 suite.

Verified: 141 v1 Python tests, 13 shared JS tests, 11 mobile tests, TypeScript, 494 contract checks, 44 new +284 prior isolated SQL checks, Expo web/Android JS exports and both Vue builds passed. No live database modification, 012 application, authenticated React/device test, upload/review/image write or deployment. **Next user step is apply only 012 once** in the existing Supabase SQL Editor as owner; then agent checks function permissions and zero-identity denial, restarts the updated API, and continues hosted writes/account/notice prerequisites. Do not repeat 001–011/password/seeds/refresh routines. See graphiscan/api/SCREENING_READS.md. Current rough overall progress 41%.

Same-slice upload correction: both legacy/API dictionary cursor count reads now use explicit report_count alias/key instead of numeric [0]. Seven isolated Python tests pass, including a simulated multipart API upload with stubbed predictor/DB for Initial and Follow-up cases. Ten React tests remain passed; no live upload/data change or concurrency guarantee. This supersedes any following unchanged-upload note for that narrow bug fix.

Latest slice (2026-10-20): connected actual report_type through all nine existing role result/list/progress queries to the React app. Parent first-visible Follow-up stays Follow-up; missing/conflicting types remain unknown. Added missing student_id projections for progress navigation. Five isolated SQLite tests execute actual read-route bodies; ten React tests, TypeScript and web/Android exports passed. No configuration/model/live DB loaded by those Python tests. Upload concurrency and hosted endpoints remain pending, not fixed by this read change; no migration/write/deployment. Overall estimate stays 38%. See latest CHANGELOG entry; do not repeat prior setup or Auth checks.

## Latest user correction and active work, 2026-10-20

User wants reuse: retain existing Vue admin, convert existing user app to React Native/Expo, implement panel suggestions, integrate Supabase and deploy. Do not treat earlier timeline estimates as limits or keep building parallel foundation screens instead of connecting the actual workflows. First conversion pass exists in graphiscan/mobile-app; it reuses the legacy /api/user contract deliberately and does not bridge Supabase tokens/UUIDs. Navigation/access/student/upload/result/review/history/profile and protected image sharing are written. TypeScript, focused tests and web/Android JS export passed; no browser/device/authenticated write verification or APK/deployment is claimed. See mobile-app/README.md. Existing Vue app remains a reference until parity. Initial dependency audit found 23 advisories, pending triage before release; no force fix/SDK downgrade. Overall rough progress 38%. Continue with parity/device checks and hosted integration, not another SQL/setup/refresh repetition. Existing v1 milestones and safe session67766 remain as recorded below.

Updated 2026-10-20 (Asia/Manila) after workspace directory UI and assignment-choice implementation. Earlier pending/setup notes are historical; newest slice takes precedence.

## Where we stopped

- Disposable Supabase setup is complete for the current read-only Auth foundation. User reported applying migrations 001–005 and seeding the fictional test profile. Do not repeat migrations, seed creation or reader-password setup.
- Agent-executed hosted TLS/read-only preflight passed all 24 checks.
- User's latest interactive `graphiscan/tools/check_v1_auth.py` report was `auth-check-passed`, all 11 checks passing: sign-in, verified identity/bootstrap, forced-password state, blocked protected features, local sign-out, provider-session revocation and denial of the original token.
- The test session was cleaned up. Report showed no application database writes and no saved credentials. Passwords/tokens must stay private.
- Latest automated evidence: **156 Python, 11 JavaScript, 494 contract and 284 isolated SQL checks**, plus both Vue builds, all passed. Both /access pages and directory modules returned 200. Browser inventory had no surfaces; visual/keyboard/live authorized form checks are unverified. Python ran outside the sandbox.
- Local `/api/v1/me/password` implementation verifies current credentials, commits pending/session denial before Auth changes, requires confirmed global logout, then clears the first-change gate with revision-bound completion/audit. Uncertain failures remain closed for recovery. `graphiscan/api/PASSWORD_CHANGE.md` documents this and fixed-fictional-account hidden-prompt recovery.
- **User reported successful hosted migration 006, writer LOGIN/password setup and `writer-configuration-saved`.** Agent-executed writer preflight now passed all **23** hosted read-only connection/catalog checks. No application/Auth record changes occurred. Initial lock-timeout failure was fixed by explicit session settings in the writer connector. Reader remains read-only. Do not repeat setup.
- **Latest user-run hosted password report: `password-check-passed`, all 12 checks passing.** Covered two verified fictional sessions, forced-change gate, password endpoint, original/other-session and old-password denial, fresh new-password bootstrap, preserved privacy gate and session cleanup. Password change was attempted and application writes may have occurred. No credentials were saved/shared. The fixture now uses the user's newly saved Auth password and has cleared first-change; do not rerun forced-first-change checkers against it unchanged.
- The earlier invalid-input attempt was blocked before sign-in/password change; no administrative Auth reset was reported or needed for the passing run.
- Existing Vue/MySQL application remains active. No client cutover/deployment or production v1 login/logout implementation has occurred. Hosted password success is user-run verified; refresh, failure recovery, real concurrency and client integration remain separate checks.

## Next work, in order

**Latest authenticated directory result:** User clicked Refresh lists and reported no error. API5002 session 67766 logged both GET /schools?limit=25 and /students?limit=25 returning HTTP200 at 09:50:19. The earlier school503 no longer reproduces on this retry; its root cause was not captured. Keep safe SQLSTATE diagnostics if it recurs. Student empty scope is user/server verified; no populated forms/writes, grants or credential changes are implied. Failed-load/empty distinction, independent list requests and permanent Refresh lists are implemented; eleven directory tests and both builds passed in the preceding fix. Do not repeat setup or ask the user to refresh again without a new failure. Next planned work is account issuance/explicit permissions and controlled fictional populated-write verification, before screening/review/release. No automatic privilege grant just to populate screens.

**Current UI/options slice:** Both /access ready states now show shared school/
student lists/forms/filters/details and eligible selectors. Read-only roles get
context only; server grants/assignments remain authoritative. New assignment-option
route makes OpenAPI sixteen foundation operations of 33. **011_assignment_options.sql
is user-reported applied**. All ten independent hosted read-only security/grant/
zero-identity checks passed. Updated API5002 is running (session 99903); live health
200, unauthenticated assignment-options 401 and admin /access 200 passed. No new
password, seed, grant or repeated migration is needed.
Next: ask the user to check the new Students/Schools sections at /access;
the fictional admin has no automatic management grant, so empty lists/hidden forms
are correct. Do not auto-grant privileges or invent populated write evidence.
See `graphiscan/api/WORKSPACE_DIRECTORY.md`. Pending creation recovery is memory
only; no durable client recovery/hosted write proof is claimed.

**Newest slice:** School/student POST and PATCH are implemented locally with
current database authorization/assignment locks, optimistic revisions, scoped
duplicate warnings and durable HMAC-bound student-creation retries. OpenAPI has
fifteen foundation operations of 33. **010_directory_writes.sql is user-reported
applied**. All 26 hosted metadata/invalid-session checks passed. Metadata was
read-only; row-locking zero-identity writer probes were explicitly rolled back,
with no application writes committed. Updated API5002 is running (session 6207):
live health 200, four unauthenticated write routes 401 and PATCH/retry-header
preflight passed. Do not repeat setup or use real student data/auto-grant privileges.
Next: eligible assignment choices and school/student screens.
Actual authorized hosted writes/retries/concurrency, assignment-option queries
and resource screens remain pending. See `graphiscan/api/DIRECTORY_WRITES.md`.

**Preceding read slice:** School/student GET lists and student detail are implemented
locally with strict filters, signed keyset cursors and database-enforced record
scope. OpenAPI has eleven foundation operations out of 33. Migration
**009_directory_reads.sql is user-reported applied**. All 15 independent hosted
read-only security/grant/zero-identity checks passed. Do not repeat setup.
Updated API is running on 5002 (session 68339); superseded GraphiScan Python
launcher/child processes were removed after stale route responses. Fresh health
200 and all three unauthenticated directory routes 401 passed. Authenticated
hosted record requests remain unverified; the fictional admin has no automatic
student-management grant. Next: controlled school/student writes and resource UI.
No resource UI or writes were added. See `graphiscan/api/DIRECTORY_ACCESS.md`.

**Latest implemented slice:** Shared v1 session login/refresh/logout and Vue
`/access` sign-in/password/privacy/readiness/sign-out are implemented locally.
Contract now has 33 operations/eight foundation operations. **008 is user-reported applied**;
all seven hosted read-only function security/grant checks passed. It adds durable
local-session revocation to the existing writer without new passwords/roles.
User confirmed admin `/access` sign-in displayed Account setup complete, then
sign-out returned to the sign-in form without an error. No seed/reset is needed.
School/student reads are now implemented by the newer slice above. Writes,
resource UI, screening, expert review and parent release remain separate work.
New `/access` wrappers use the separate updated local API on **5002** through
ignored public `VITE_HOSTED_API_ORIGIN`; record clients remain on original 5000.
Both frontend routes/modules/origin/CORS and safe hosted health/invalid-request
responses passed, as did legacy health. Some original Windows listeners kept
old routes after stop attempts; do not use their 404s as current hosted evidence.
Hosted browser sign-in/readiness/sign-out is user-reported successful. Refresh,
revoked-token replay and independent visual inspection remain unverified here.
See `graphiscan/api/SESSION_INTEGRATION.md`. Resource migration is still needed;
the new account-ready state does not route hosted tokens into MySQL dashboards.

**User communication preference:** Include overall percentage in every progress
update and final response. Latest rough full-scope estimate is **about 35%**;
not measured completion and not a guarantee of afternoon readiness. Update only
when material evidence justifies it. Keep guest work stopped.

**Latest user steering:** Stop guest-demo testing and focus on the agreed core
scope; user is planning to remove the demo. Actual guest UI/API/role removal is
not implemented. Do not resume the guest-screening step in older notes below.
Panel minutes do not require guest demo; the design lists it as optional.
Prioritize actual shared login/logout and client password/privacy integration,
then teacher screening, expert validation, parent release, school/grade grouping,
Initial/Follow-up history and supported model evidence. Preserve broader agreed
API/native/model/document work; page-load rehearsal is not core implementation.

Presentation steering: user targets approximately **2-3 PM today, Asia/Manila**.
At the 7:43 AM check about 6-7 hours remained. See `PRESENTATION_READINESS.md`.
Full-rebuild planning estimate is roughly 25-35% (about 30%), not measured
completion. Asked whether the presentation expects an existing prototype/progress
demo or the full revised release. Proposed priority is fresh demo rehearsal and
evidence material; scope is not yet confirmed and no requirements are removed.

Latest update: user supplied **`privacy-check-passed`, all nine checks passing**,
including exact notice, explicit saved acceptance, stable repeat timestamp,
stale-version denial, bootstrap/gate readiness and session cleanup. The earlier
no-acceptance publication inspection is historical. No credentials were saved or
shared and no password changed. Do not repeat the completed onboarding checks.

1. Read current `AGENTS.md`, knowledge/changelog, contract and `graphiscan/api/PASSWORD_CHANGE.md`. Local implementation/testing is complete; do not repeat Auth fixture creation or migrations 001-005.
2. User authorized a temporary **fictional-account** test notice, revisable later. **007 is user-reported applied and notice publication is independently read-only verified.** Do not rerun migration/seed or repair the repeat-run error without new evidence; the saved state is correct.
3. **Hosted user-run privacy acceptance/round-trip now passed.** Fresh existing-stack presentation baseline: both Vue production builds and all 26 read-only local API checks passed. Local Flask (127.0.0.1:5000, debug/reloader off), admin Vite (5173) and user Vite (5174) were started and intentionally remain running; frontend roots returned 200. Next is real browser sign-in/rehearsal with existing MySQL app accounts, not the fictional Supabase account. See `PRESENTATION_READINESS.md`. Real-use wording/approval/retention inputs, generic login/logout, refresh/concurrency/recovery and client integration remain separate work.
4. Resource endpoints, private storage and migration remain later work. Preserve active Vue/MySQL behavior until verified cutover.

Next focus is the existing demonstration app and rehearsal. Temporary fictional onboarding has passing user-run hosted evidence; real-use privacy wording remains unresolved. No agent-hosted mutation or credential disclosure occurred. Do not repeat 001-007, either seed, writer/reader/password setup or passing onboarding checkers.

Dashboard update: user confirmed the existing admin sign-in/dashboard loaded.
Browser connector inventory returned no available tabs, so authenticated UI
inspection is not independently verified. Use `PRESENTATION_REHEARSAL.md` for
manual Users/Students/Results/Progress/Settings/Audit checks and speaking order.
No extra login/browser setup is needed; local demo services remain running.

Latest rehearsal update: user reports all requested admin pages load (Users,
Students, Results, Progress, Audit Logs, Settings; Dashboard already confirmed).
Record this as user-reported navigation, not full visual/write/detail coverage.
Next is existing user-app teacher login/student/result rehearsal on port 5174,
then expert and parent views with existing demo accounts. No new credentials,
real-student upload or record edits are needed for the read-only first pass.

Teacher rehearsal update: user confirmed dashboard, students, results list and
one existing result work. This is user-reported navigation/detail evidence, not
new upload/inference verification. Next: expert dashboard/results/review view
without submitting changes, then parent released-result view using existing
demo accounts. Keep presentation checks focused and local services running.

Expert rehearsal update: user confirmed dashboard/results/existing review page
including image/details work. No validation submission was tested. Next is
parent dashboard and linked reviewed-result list/detail using the existing demo
account; a correct empty reviewed-results state is possible. Do not alter review
status/record links just to populate the demonstration.

Parent update: user reported the view works; populated reviewed-result availability
was not separately confirmed. All four role read-only screen walkthroughs are now
user-reported working. Before fresh inference rehearsal, fixed two broken guest
dashboard card links to `/guest/demo` (API path remains `/guest/demo-screening`);
user-app rebuild passed. Next is existing guest account + synthetic handwriting
sample in Demo Screening. No official student result is created, but source writes
a guest audit event and cleans up the temporary upload. Actual new inference and
expert validation submission remain unverified in this rehearsal.

Related records: `PROJECT_PLAN.md`, `WORK_CHECKLIST.md`, `graphiscan/api/HOSTED_PREFLIGHT.md`.
