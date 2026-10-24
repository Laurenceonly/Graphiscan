# GraphiScan consolidated work checklist

## Current reconciliation - 2026-10-24

Publication/progress: all reviewed public source is committed/pushed and PR#11
is confirmed merged; Vercel preview READY and admin preview user-viewed. Source
publication is complete for the current slice. Approximately65% overall; next
private image/expert/parent/Follow-up, then admin/native/release checks. Historical
data/images, three-class evidence, approved real-use privacy and paper/deck remain
open. Prior local-only/publication-pending paragraphs below are historical.

Latest screening evidence: user supplied the first completed MobileNetV2 Initial
Screening browser result, Normal49.19%/High Potential50.81%, expert Pending.
PR#10's upload fix is merged;35 isolated regressions pass. Next verify private
image, assigned expert review, parent release/denial and Follow-up. This is supplied
browser evidence, not independent API/latency/accuracy or complete role/native
verification. The older prediction-pending notes below are historical.

Saved-session status: approximately65% overall. PR#9 is merged, private model
fetch verifies all3, and supplied Render logs show successful one-thread model-host
startup and Live. User saw model choices; actual prediction is still unverified.
Full-height list skeletons and minimal search affordances now cover native app
roles locally. TypeScript/browser role checks and native loading captures pass;
native search/modal/Back and full workflow remain open. RESUME.md is the active
restart guide. Later dated paragraphs below preserve earlier evidence boundaries.

Logout/loading follow-up: shared manual sign-out confirmation and missing feed
skeletons implemented; query changes hide stale content and refresh preserves the
current page.14 fictional UI cases,18 mobile/19 shared tests, TypeScript and
1296-module Android export passed. Native modal/Back review remains pending.
User confirmed native pages work before this slice; no actual logout/write ran.

Continuation: final11 fictional directory browser checks,18 mobile/19 shared
tests and TypeScript passed. Picker theme recapture/design notes are complete.
GraphiScan_Pixel_6 API36 emulator and official Expo Go58.0.5 are installed;
native login rendered in light/dark and dark font_scale1.3. Android height
keyboard avoidance fixes covered login actions, confirmed in native recapture.
Final TypeScript/Android export passed1295 modules. Expo Go configuration reload
failure remains an observed development limitation; fresh-process recovery worked.
User confirmed private native hosted sign-in after a wait. Role workflows remain
unverified; the original sign-in latency/cause was not captured.
npm run preview:android fixes IPv4 localhost
access through adb reverse. Native hosted roles, APK and physical-device checks
remain open. Overall estimate remains60–65%.

Use [CURRENT_REQUIREMENTS.md](CURRENT_REQUIREMENTS.md) for the current requirement
matrix and next steps. Admin/API are published, user confirmed login/dashboard,
Render follows main. Migrations through021 are installed and the last required
hosted restricted preflight passed38 checks; PR#5 assignment source and PR#6
shared admin alignment are published. Expo hosted onboarding, role workspaces,
student create/edit and server filters are implemented locally; no APK exists.
Full-project planning estimate is approximately65%; see the dated workstream
review in CURRENT_REQUIREMENTS.md. Latest mobile follow-up is being checkpointed locally.
Do not repeat old setup. Full hosted account/assignment actions and role flows,
actual hosted prediction/three-class work, Expo APK/device work, legacy-data cutover and
manuscript/privacy approval remain open. Earlier dated checkpoint paragraphs
below are historical, not fresh migration instructions. No tests ran for this audit.

Current admin release (2026-10-22): user deferred Expo and resumed admin completion/deployment. Source includes full account actions with prepared019; corrected019 compiled locally and lifecycle catalog flags passed. Hosted019, real reset/delete/status verification and deployment remain pending. Both Vue builds, Python syntax/factory/source-secret review and fictional dialog inspection passed. Vercel login/PR#1 confirmed; Render login needed. No deployment/private key transfer. See `graphiscan/api/ADMIN_RELEASE.md`; older paused/source-limit checkpoints below are historical.

Latest budget direction (2026-10-22): model hosting must be free; Cloud Run is on hold while account/card and free-tier memory constraints are resolved. Portable backend container/factory files and the admin build are prepared;35 focused Python checks pass. No paid model resource, server-secret upload, image build or live deployment occurred. Latest source is being saved on `deploy/free-hosting`, with Vercel auto-deployment disabled for that preparation branch. See `graphiscan/api/HOSTING.md`; earlier hosting checkpoints below are historical.

Hosted checkpoint (2026-10-21): Supabase schema migrations are installed through017 and the separate admin writer setup passed23 read-only hosted checks. No account or other hosted records were changed. Local MySQL recovery is paused by user direction; MariaDB still stops on the crashed `mysql.db` privilege table. No fresh logical source export or Supabase data import exists. Continue hosted app work. Vercel SPA config exists, but the configured hosted API origin is loopback; host Flask on public HTTPS and set Vercel environment before frontend deployment. Do not claim legacy-data migration, reconciliation, or cutover complete.

MySQL startup issue (2026-10-21): initial XAMPP logs showed Aria log write/checkpoint errors. A hash-verified offline copy is preserved at `.local-backups/mysql-offline-20261021T143247Z-9cfff3` (file copy only, not SQL restore evidence); `aria_log.00000001` was restored after the diagnostic move caused a missing-log startup error. With user approval, only the live `mysql.global_priv.MAI` index was replaced using an intact index validated on a copy; the previous live index is preserved in `.local-backups/mysql-recovery-indexonly-20261021/`, and `.MAD`/application tables were not replaced. MariaDB still stops because `mysql.db` is marked crashed. User redirected focus to hosted work; local repair and data migration are paused. Do not claim migration readiness.

Account-update implementation checkpoint (2026-10-21): source migration `017_account_management.sql`, the protected PATCH API, and hosted Users edit form are implemented. Isolated migration/workflow suite passed168 checks, OpenAPI/contract suite passed494 checks, and admin production build passed. `git diff --check` reported only CRLF conversion warnings. Migration 017 has not been applied to Supabase; latest hosted schema remains016. Account issuance/password reset and hosted role workflows remain open. No hosted database or account writes were made.

016 installation verified (2026-10-21): user-applied bundle and both test-admin grants independently passed14 hosted checks. API5002 current source restarted; health200/new anonymous routes401. No repeat setup needed. Fresh signed-in Users/Audit list confirmation pending, followed by substantial reference-based UI refinement and deployment review. Agent made no hosted database writes.

Hosted admin surfaces (2026-10-21): shared workspace, main panel, content and page-background token now use white; enclosed cards retain light borders. Dashboard spacing is more open and its no-record state uses a centered full-width panel. Source updated; final browser/build verification is pending. No backend/model/data changes.

Hosted admin spacing (2026-10-21): page inset, section gap, panel/card padding, metric dimensions and control spacing now share desktop/mobile values across all hosted pages. Admin production build passes; visual check after this adjustment remains pending.

Immediate SQL handoff (2026-10-21): run only `016_admin_reads_setup.sql` once in existing disposable test project; it includes migration and exact fictional-admin read grants. Hosted read-only check confirms 016 missing. After user success: run new `check_v1_admin_setup.py --connect`, restart exact hosted API5002 listener to load new routes, fresh sign-in and inspect populated Users/Audit. 146 isolated SQL checks passed; no hosted writes. Reference-based UI redesign remains unapproved after user rejected the subtle pass. Deploy after UI and runtime checks; deployment not started.

Current hosted admin checkpoint (2026-10-21): page alignment and typography refined across Students, Results, Progress, Users, Audit and Settings; dashboard condensed using user dashboard screenshots while retaining GraphiScan navigation. Users/Audit now have read-only code paths and UI tables, verified only against isolated SQL and fictional browser data. Migration 016 and separate global grants are pending in hosted setup, so these pages must not be reported as live/populated. Account actions and real end-to-end workflows remain open. Build, isolated tests and six-width synthetic browser checks passed.

Hosted admin page checkpoint (2026-10-21): all eight original sidebar choices render and fit across six tested widths. Dashboard, Students/Schools, Results, Progress history and Settings password flow are connected and synthetically checked. Users/Audit Logs are still unavailable pending new scoped v1 endpoints and account actions; never claim these screens as functional. Admin/user builds, 53 navigation/page checks, 16 screening checks and dashboard/modal regressions passed with intercepted responses only. Real populated hosted workflow remains pending.

Responsive admin login refinement (2026-10-21): user approved tightening layout and improving responsiveness. Form now max380px (was340), logo64px (was56), clearer28px heading/14px labels,50px inputs/48px submit; retained upper-left branding, flat button and16px field text. Shell height adapts to viewport; tablet collapses to single-column at980px, phone padding corrected and short-laptop/landscape rules added. Preview reduced to560-700px and tilt12deg so more dashboard is visible. Password placeholder shortened for320px. Final admin build passed; nine browser sizes1920/1440/1366/1024/980/768/390/320/844-landscape passed horizontal fit, brand/form separation, empty inputs, stable focus size,44px controls and reachable submit;1366x768 fits vertically, landscape scrolls naturally. Screenshots inspected, final320px confirmed. No Auth/backend/mobile changes.


Single main admin entry (2026-10-21): user was confused by Admin Web Panel versus workspace. Canonical admin /login now serves hosted admin/researcher flow; / and /access redirect there. No visible workspace-switch links. Old MySQL login is explicitly /legacy-login, with old /admin/* guards, API401 redirects, logout/password-success redirects, tools and old Flask admin-login return updated accordingly. Hosted sessions are never bridged to legacy tokens. Shared component adds default-preserving display props; Vue user and Expo role allowlists unchanged (teacher/expert/parent). Both Vue builds,15 intercepted entry/role/redirect/isolation checks and12 existing hosted workflow checks passed; no real credentials/provider writes. Flask redirect source changed but legacy server behavior not runtime-tested/restarted. Modern reference review: official shadcn login/signup and Clerk sign-in; inspected shadcn two-column login visually. Reference-inspired visual changes beyond existing design are recommendations only; retain approved blue panel/wording. Updated admin README. Next remains admin UI refinement, then first hosted teacher upload/review/release.


Admin UI priority (2026-10-21): user chose admin first and requested the same design with better consistency. Implemented admin-only hosted styling in admin-web/src/views/HostedAccess.vue matching the existing blue/white Inter identity; shared user components unchanged. Added control tokens and consistent page titles, primary/secondary buttons, form borders/radii and filter heights in admin-web/src/style.css. Final admin build passed; 12 existing all-intercepted hosted browser checks passed. Seven legacy admin pages checked at1440/390px with synthetic empty responses:14 fitting layouts, matched heading scale, no page exceptions; Add User dialog open/Escape and hosted password toggle checked. Desktop/mobile screenshots inspected. This is visual/mock verification, not live legacy data or new hosted writes. UI is the current priority; first hosted teacher upload/assignment/review/parent-release remains pending. Keep current identity; no mobile changes requested.


Latest directory verification (2026-10-20): user reported no error after Refresh lists; API67766 confirms authenticated school and student GETs both returned HTTP200 at 09:50:19. Earlier school503 did not recur; root cause was not captured, so safe diagnostics remain without claiming a DB/permission repair. Scoped read success does not establish populated fixtures or write flows. No DB/grant/account/credential change or repeated tests. Next planned: account issuance/explicit permissions and controlled fictional populated-write verification, then screening/review/release. No automatic privilege grants; no need to repeat refresh/setup absent new failure. Rough full-scope progress stays 35%. Earlier active-error notes below are historical.


Directory retry evidence (2026-10-20): user applied filters and reported no students; authenticated /students?limit=25 returned HTTP200 in API67766 logs, confirming successful empty scoped student view. Earlier /schools503 still needs authenticated retry. Added persistent Refresh lists so both resources can be retried even after successful student filtering clears the shared error; both Vue builds passed. Next: user clicks Refresh lists, inspect API67766. No database/grant/credential change or claimed root cause; overall estimate stays 35%.


Active directory defect (2026-10-20): user sees Account setup complete and Students/Schools, but authenticated /schools returned 503. This is not a confirmed empty result. Diagnostic API5002 session 67766 now logs SQLSTATE only; user was asked to retry records so the failure code can be traced. UI now distinguishes not-loaded/empty and loads lists independently. Eleven directory tests and both Vue builds passed; valid-user fetch/root cause remain unresolved. JIT was already disabled, so no JIT change was made. Fix this before new features. No DB/grant/credential changes; rough progress stays 35%. Older successful metadata/zero-identity checks are narrower evidence.


Latest assignment setup checkpoint (2026-10-20): 011 is user-reported applied and all ten independent hosted read-only metadata/zero-identity checks passed. No writes, credentials, grants or records changed. Updated API5002 is running (session 99903): live health 200, unauthenticated options 401 and admin /access 200. Next: user signs in with the existing fictional Auth account/current password and confirms Students/Schools sections. Empty scope can be correct; no automatic management grant or populated-write evidence is implied. Overall rough progress remains 35%. Older installation-pending notes below are historical; do not repeat SQL/password/seed setup.


Latest workspace/options slice (2026-10-20): both /access ready states now include shared school/student lists, filters, details and forms, eligible teacher/parent selectors, revision recovery and explicit same-payload student creation retry. New assignment-options read route is local; UNAPPLIED 011 adds only an existing-reader fixed-path definer read capability, no data/grants/credentials. 156 Python/11 JavaScript/494 contract/284 isolated SQL checks and both Vue builds passed. Vite pages/modules returned 200; browser inventory was empty, so visual/live authorized form checks remain unverified. Next: apply only 011 once, verify hosted function metadata/zero-identity denial, restart API5002 and user-check Students/Schools sections. No automatic privilege seed or data migration. Rough overall progress is 35%; earlier checkpoints below are historical. See graphiscan/api/WORKSPACE_DIRECTORY.md.


Latest hosted mutation checkpoint (2026-10-20): 010 is user-reported applied. All 26 hosted metadata/invalid-session checks passed. Metadata was read-only; row-locking zero-identity writer probes were explicitly rolled back, with no application writes committed or private data/key output. Updated API5002 (session 6207) passed live health 200, four unauthenticated write routes 401 and PATCH/Idempotency-Key preflight. Authorized hosted writes/retries/concurrency and resource UI remain pending. Next: eligible assignment choices and school/student screens. No repeat SQL/password/seed setup. Rough overall progress remains 34%; older installation-pending notes below are historical.


Latest directory mutation slice (2026-10-20): school/student POST/PATCH are implemented locally with scoped assignment checks, profile/record locks, optimistic revisions, private duplicate warnings and durable HMAC-bound student creation retries. Unapplied 010 reuses the existing function-only writer, initializes a private random request-digest key and adds no application records/grants or new credentials. 151 Python/494 contract/265 isolated SQL checks passed; OpenAPI has fifteen foundation operations of 33. Next: apply only 010 once, inspect hosted permissions/zero-identity denial and restart API5002. Actual hosted writes/concurrency, assignment-option queries and resource UI remain pending. Rough overall progress is 34%; older checkpoints below are historical.


Latest hosted directory checkpoint (2026-10-20): 009 is user-reported applied. All 15 independent read-only function security/grant/zero-identity checks passed; no hosted writes or private record output. Updated API5002 is running: live health 200, three directory routes 401 without bearer after stopping superseded GraphiScan Python processes. Authenticated hosted record/scope requests and record UI/writes remain separate work. Do not repeat migrations/password/seed setup. Rough overall progress remains 33%. Older installation-pending notes below are historical.


Current directory checkpoint (2026-10-20): school/student lists and student detail
are implemented locally, with strict filters, signed cursors and current
database-enforced scope/gates. 140 Python/494 contract/210 isolated SQL checks
passed. Migration 009 remains unapplied; it adds only a restricted read function
to the existing reader, no credentials/data/table grants. Next: apply 009 once,
verify hosted metadata and restart API5002 before scoped read checks. Resource
writes/UI, screening and private images remain open. Rough overall progress is
**33%**; preceding-slice checkpoints below are historical.

Hosted 008 update (2026-10-20): user reported migration success; independent read-only catalog inspection passed all seven logout-function security/grant checks. No hosted writes or function invocation occurred. Do not repeat setup. User confirmed admin browser sign-in displayed Account setup complete and sign-out returned to the sign-in form without error. This is user-reported evidence; hosted refresh/revoked-token replay and independent visual checks remain separate. Next implementation is authorized school/student resource access before screening/review/parent-release migration. Overall progress remains approximately 32%.


Reviewed 2026-10-17 against all nine project Markdown files (excluding dependency, tooling, backup, and generated directories). This is a document-based baseline, not a fresh code or runtime audit. Boxes are checked only when the stated item has evidence. Partial work is noted below. Follow both comments and committed actions in the defense minutes. Panel numbers refer to PROJECT_PLAN.md.

## 1. Preparation and recovery

Session/client checkpoint (2026-10-20): shared v1 login/refresh/logout and Vue `/access` onboarding are implemented locally; unapplied 008 grants the existing writer durable local-session revocation without new credentials. Next: apply only 008 and verify actual hosted browser sign-in/readiness/sign-out. 129 Python/seven client-JS/494 contract/165 SQL checks and both builds passed. New onboarding uses local API5002; existing records remain MySQL/API5000. Resource migration, native persistence, real concurrency/recovery and full cutover remain open. User requests every update include a rough percentage; latest full-scope estimate about32%.

Hosted privacy lifecycle passed (2026-10-20): user supplied nine passing checks including explicit saved test-notice acceptance, repeated timestamp, stale-version denial, bootstrap/gate readiness and cleanup. No credentials saved/shared; no password change. Do not repeat onboarding setup/checkers. Fresh admin/user Vue builds passed; presentation work now needs the local API result and browser/role rehearsal. Existing release/privacy/client/resource boxes remain open; test notice acceptance is fictional participation only.

Hosted notice publication checkpoint (2026-10-20): user ran the seed twice and reported a repeat error. Agent read-only verification passed all eight publication/function metadata flags; one correct current scoped notice exists and no acceptance is recorded. Do not repeat/repair setup. Next is the explicit hidden-prompt privacy checker; hosted acceptance/concurrency/client verification remain open. No runtime edits or repeated tests in this checkpoint.

Hosted privacy setup update (2026-10-20): user reported 007 applied successfully. Next is `seed_test_agreement.sql`, then explicit interactive test acceptance. Neither publication nor acceptance is yet reported complete. Do not repeat migrations/password setup. Local test evidence remains 118 Python/466 contract/151 isolated SQL; this checkpoint changes documentation only.

Temporary notice checkpoint (2026-10-20): user authorized temporary fictional-account test wording, revisable later. Canonical test notice and local versioned GET/acceptance/scoped database function/checker are ready; 118 Python/466 contract/151 isolated SQL checks passed. 007, optional fixture publication and actual hosted acceptance remain pending. Existing writer credentials are reused. Real-user wording/approval/retention and hosted concurrency/client cutover remain open; test acceptance is not real student-data permission.

Privacy wording status (2026-10-20): user confirmed unavailable. Internal inputs are saved in `PRIVACY_REVIEW_BRIEF.md`; no agreement has been drafted as approved, published or accepted. Generic login/logout/session work can proceed independently. Agreement publication/real acceptance and client cutover remain dependent work; the missing-agreement gate stays closed.

Password lifecycle checkpoint (2026-10-20): user supplied all 12 passing hosted password checks, including actual endpoint, old-password/original/other-session denial, fresh new-password bootstrap, privacy denial and cleanup. Fixture first-change is now cleared; do not repeat its forced-state checker unchanged. No credentials were saved/shared; a change was attempted and application writes may have occurred. Next: approved privacy wording/version and agreement acceptance/gates, then client integration. Generic login/logout, refresh/concurrency/hosted recovery and production/resource gates remain open. Documentation-only update; latest local tests remain 103 Python, 465 contract and 123 isolated SQL.

Hosted writer checkpoint (2026-10-20): private writer configuration reported saved; 23 actual read-only writer login/catalog checks passed. Fixed explicit session lock/statement/UTC setup after the first lock-timeout failure. Prepared `tools/check_v1_password.py` for a manual hidden-prompt fictional Auth password change and old-credential/session checks. All 103 Python, 465 contract and 123 isolated SQL checks passed. No actual Auth password/application record changed yet; hosted password/recovery/concurrency/client gates remain open. Do not repeat setup or enter database-role passwords in the Auth checker.

Writer setup update (2026-10-20): user reported successful separate writer LOGIN/password setup. Private writer DSN setup is next via `graphiscan/tools/configure_v1_password_writer.py` (six new synthetic tests passed). Do not repeat migrations/password setup. Actual writer connection/grants and hosted password/session checks remain open; no private password or connection string was received.

Hosted password setup update (2026-10-20): user reported successful migration 006 execution. Its unapplied status below is historical. Next: private separate-writer LOGIN/password, writer DSN and hosted verification. Reader stays read-only. No agent-hosted write or independent 006 grant/connection verification occurred; local test totals remain 84 Python, 465 contract and 119 isolated SQL.

Local password checkpoint (2026-10-20): v1 password change/session invalidation and fixed-fixture recovery implemented; 84 Python, 465 contract and 119 isolated SQL checks passed. Migration 006 is unapplied; separate writer setup and hosted password/old-credential/session/recovery checks remain open. The reader stays read-only; no actual Auth password was changed. See `graphiscan/api/PASSWORD_CHANGE.md`. This supersedes the implementation-next checkpoint below; production/client/privacy completion boxes remain open.

Passing hosted Auth checkpoint (2026-10-20): user supplied all 11 passing interactive checks, including verified bootstrap, forced-password gate and revoked-session denial. No application writes or saved credentials. This supersedes the failed-run note below. Production v1 password/session endpoints and client onboarding remain open; next is password-change/session-invalidation implementation. Documentation-only update; no repeated tests.

Auth troubleshooting checkpoint (2026-10-20): first interactive sign-in failed before session creation. Actual Auth settings accepted the key and enabled email login. Safe failure diagnostics added; 61 Python tests passed. A user-controlled retry is pending; successful hosted Auth/bootstrap/logout boxes remain open.

- [ ] Obtain the editable manuscript, presentation, approved privacy agreement, hosting access, and an Android test device; agree on demonstration scope and owners.
- [x] Export the current authoritative MySQL database, back up images and configuration securely, and prove the backup restores. Retain the current working system during migration. Verified 2026-10-17: 8 tables restored with matching schemas/content; project/private-assets archive passed integrity checks. Application boot from extracted assets and an off-machine backup remain separate checks.

## 2. Finish the Vue admin (panel 2, 3, 5)

Evidence updated 2026-10-19: real user-assisted login and all seven populated admin routes passed at desktop/phone widths. Searches, sampled filters/detail/back links, navigation, student view, and safe form checks passed. Fixed pending-result image generation and confirmed the actual image loads. The 26 live API status checks and 8 synthetic tests passed. Ten isolated API write checks and twenty browser assertions passed on desktop and again at 390px using fictional accounts and a disposable database; source fingerprints were unchanged after cleanup.

The accessibility pass fixed explicit field/button names, required indicators, modal/drawer keyboard handling, focus entry/containment/return, background inertness/scroll lock, alert/status roles, small controls, and contrast. The final build and bounded Chromium checks at 320px/390px/1440px passed for the sampled forms. Simulated slow/503/offline/empty user-list states and failed-save/retry checks passed, including retained input and disabled pending saves. Complete screen-reader/physical-device checks, text zoom, additional error cases and other-role/older Flask flows remain release work; the core admin baseline is ready for API contract work.

- [ ] Verify and fix dashboard, user/account, student, result, progress, settings, and audit workflows using populated records and real role login.
- [ ] Finish comprehensive readability/classification, accessibility, responsive/detail, and error-state coverage. The bounded automated pass above is complete; manual screen-reader, text-zoom, physical-device and remaining error cases are still open.

## 3. Shared API, database, authentication, and private images

Interactive Auth preparation (2026-10-20): user reported fictional profile seed success. Hidden-prompt checker and nine synthetic tests are ready (58 Python tests total). Actual hosted sign-in/bootstrap/local logout/durable session denial requires the user's private interactive run. Application DB writes and v1 session/onboarding endpoints remain unimplemented; related completion boxes remain open.

Auth fixture preparation (2026-10-20): user reported creating the fictional auto-confirmed Auth account. Optional guarded `seed_test_profile.sql` and seven isolated fixture checks are ready; latest contract/SQL totals are 464/91. Hosted profile seed and actual user-token bootstrap remain pending. No account password is recorded and no full Auth completion box is checked.

Hosted read-only verification (2026-10-20): 24 actual preflight checks passed with verified CA/TLS and restricted reader login, current SELECT-only grants/RLS/trigger/function metadata and zero-identity denial. No DB writes; real user token bootstrap was not run. Fixed Auth-catalog inspection and passed 49 Python, 464 contract and 84 isolated SQL checks. Full Auth/resource/migration boxes remain open; next is a fictional Auth test identity.

Reader checkpoint (2026-10-19): user reported matching 20-table/20-RLS/trigger metadata after 001-004. New unapplied 005 adds a NOLOGIN server reader, six SELECT policies and restricted definer Auth-session lookup; runtime query/preflight now account for real Auth RLS. Passed 49 Python tests, 464 contract checks and 83 isolated SQL checks. User execution of 005, private login/password/DSN setup and hosted verification remain pending; completion boxes remain open.

Hosted preflight preparation (2026-10-19): offline-by-default read-only checker and `graphiscan/api/HOSTED_PREFLIGHT.md` are ready. The local check found four missing v1 settings and attempted no network/DB writes. All 48 Python tests, 464 contract checks and 73 isolated SQL checks passed. A disposable target, reviewed schema/reader setup and optional fictional-user session are still needed for actual hosted evidence; related completion boxes remain unchecked.

Adapter checkpoint (2026-10-19): optional trusted Auth/PostgreSQL adapters and unapplied 004 session invalidation now exist. Passed 38 Python tests, 464 contract checks, 32 prior SQL checks and 31 access-query/security checks with fictional Auth tables. Configuration/TLS options were checked with the installed driver without connecting. Hosted provider/TLS/grants/concurrency verification and session/onboarding writes remain open; durable authentication is not marked complete.

Runtime foundation (2026-10-19): `/api/v1/health`, `/me`, and a shared guard now exist with synthetic runtime tests for onboarding, account/session denial, explicit grants and callback-based record access. Default identity/profile adapters remain unavailable and deny protected access with 503. This does not complete durable authentication, PostgreSQL query conversion, resource routes, or the proposed 19 end-to-end access scenarios.

- [ ] Finalize shared contracts for accounts, schools, students, screenings, models/versions, reviews, reports, and protected images. `API_CONTRACT.md` and OpenAPI now cover 31 proposed operations; 19 integration cases are specified. Offline validation passed 464 schema/declaration/payload checks. Shared-guard synthetic runtime tests now pass; real-resource integration tests, policy-dependent choices and contract freeze remain open.
- [x] Apply and verify staged Supabase/PostgreSQL schema through021 in the hosted project. User application and the last38-check restricted read-only preflight are recorded in `CHANGELOG.md`; do not repeat migrations or permission setup. This does not complete legacy data/image migration.
- [ ] Complete runtime cutover: retire/convert the remaining MySQL Flask routes, migrate a reviewed copy of records and images, reconcile counts/relationships/history, and test rollback before cutover. Existing Supabase v1 APIs are a parallel path; this is not yet a full MySQL-to-Supabase data or application cutover.
- [ ] Map old user IDs to Supabase Auth identities; replace in-memory tokens with verified durable authentication. Do not reuse old reset tokens or import password hashes as usable credentials.
- [ ] Migrate a copy of records and images; reconcile counts, relationships, school/grade assignments, historical reviews, report order, and score units. Preserve historical binary model identity and labels; exclude obsolete AI advice.
- [ ] Move images from public Flask static storage to private Supabase Storage with server-authorized access.
- [ ] Test migration rollback before cutover. Keep the old database until replacements are verified.

## 4. Accounts and authorized access (panel 10; panel 3 workflow)

- [ ] Finish administrator/explicitly authorized researcher account issuance with temporary passwords; retain blocked public registration.
- [ ] Enforce password change on first login, then acceptance of the approved versioned Data Privacy Agreement before other protected features. Store acceptance version/time; resets must preserve onboarding gates.
- [ ] Enforce disabled-account, role, ownership, school/student assignment, and expert assignment rules in Flask. Cover JSON APIs and older Flask pages until retired.
- [ ] Verify parents can access only linked, expert-validated reports and images. Existing synthetic parent-access tests passed; live flows/private storage still need verification.

## 5. Schools and students (panel 9)

- [ ] Add school management and required student school/grade assignment, retaining the separately agreed Grades 1–3 scope.
- [ ] Add school/grade grouping, filters, and summaries across applicable API/admin/mobile views; validate duplicates, assignments, and access.
- [ ] Match participant scope and grouping in the manuscript. The minutes specify elementary students; Grades 1–3 comes from the separate project scope.

## 6. Models and screening (panel 1, 2, 5, 11)

- [ ] Train/evaluate ResNet, EfficientNet, and MobileNet on a common documented three-class split; record accuracy, per-class precision/recall, confusion matrices, preprocessing, and dataset/writer-separation limitations.
- [ ] Integrate all three evaluated models, use the highest-accuracy model as default, and provide manual teacher model selection.
- [ ] Implement consistent Normal / Low Potential / High Potential inference, storage, and display after three-class validation. Current inference is binary; preserve old binary history without relabeling it.
- [ ] Store model key/version, task type, class scores, classification, screening type/date, and review status with each result. Describe scores as model outputs, not clinical probability.
- [ ] Validate uploads and student access; failed/demo uploads must not create official assessments.
- [ ] Guarantee exactly one Initial Screening per student, including concurrent submissions; automatically classify all later completed assessments as Follow-up Screening. Hosted completion locks the student and retains the unique Initial invariant; isolated competing-reservation tests pass and migrations through021 are applied. Live multi-connection verification remains pending; do not rerun old migrations to resume. Legacy count-based labeling is still partial.
- [ ] Keep AI recommendations absent from inference, APIs, displays, reports, and manuscript; clean obsolete stored advice/columns during migration. Existing source removal is partial.

## 7. Expert review, reports, and progress (panel 3, 11)

- [ ] Complete authorized expert review with image, student/history, model, score, Validated/Flagged decision, reasoned remarks, and audit history.
- [ ] Attribute any justified professional recommendation to the expert and review date. Keep provisional/flagged classifications withheld from parents.
- [ ] Complete reports with school/grade, screening type/date, authorized image access, model/version, classification, model score, and expert status/remarks.
- [ ] Show dated Initial/Follow-up history; compare only compatible model/task scores and avoid unsupported improvement claims. Verify the teacher-to-expert-to-parent flow end to end.

## 8. Native Android app (separate agreed architecture work)

- [x] Build React Native + Expo + TypeScript shell and shared API integration. Hosted native sign-in is user-confirmed; source/type/export/browser checks and native login/loading captures exist. Full workflow and APK are separate gates below.
- [ ] Implement login/password/privacy gates, teacher student/capture/upload/model-selection/results/history flows, expert review, parent released reports/history, and isolated guest demo.
- [ ] Verify permissions, navigation, failures, usability, and all core role workflows on a physical Android release build. Retain Vue/Capacitor until parity is demonstrated.

## 9. Manuscript and presentation (all panel items)

- [ ] Revise objectives around analysis and justified recommendations; add expert validation (3).
- [ ] Name ResNet, EfficientNet, and MobileNet and explain their purpose; report comparable evaluation methods/results (1, 4).
- [ ] Remove unsupported AI advice; describe expert recommendations accurately (2, 3).
- [ ] Strengthen Background: problem, gap, significance, pages 2–5 (6).
- [ ] Organize literature into 3–4 themes with italicized headings, pages 10–12 (7).
- [ ] Revise scope for elementary participants grouped by school/grade, reflecting agreed Grades 1–3 (9).
- [ ] Describe team-issued accounts, first-login password change, agreement acceptance, expert validation, and Initial/Follow-up workflow (3, 10, 11).
- [ ] Replace methodology image with Integrated Hybrid Project Management Approach, page 24 (12).
- [ ] Remove unnecessary WBS components and align WBS with that approach, page 26 (13).
- [ ] Include interactions shared by at least two actors and merge/reorganize the Use Case Diagram, page 38 (8, 14).
- [ ] Align DFD and CFD and related text, pages 39/41 (15).
- [ ] State measurable nonfunctional requirements, pages 34–36, and substantiate them with final-system checks (16).
- [ ] Improve text colors/fonts, make classifications clear, and smooth presentation slide transitions (5).
- [ ] Ensure final paper/slides match deployed behavior and evidence. Editable manuscript and deck remain needed for review.

## 10. Hosting, release, and ongoing tracking

- [x] Provision the agreed existing free hosting foundation: Vue admin on Vercel, Flask/Gunicorn with the private LiteRT model bundle on Render Free, and Supabase Auth/PostgreSQL/private Storage. PR#9 merged and model-host build/startup/health pass; actual hosted prediction and release checks remain open. Cloud Run is no longer the active deployment path. Server-only secrets remain outside Git.
- [ ] Recheck provider terms/costs before deployment; old recorded estimates are not current guarantees.
- [ ] Disable Flask debug deployment, restrict CORS origins, use a production server, and align or retire older Flask pages.
- [ ] Run populated role/access, onboarding, private-image, report/history, simultaneous-upload, model/version, responsive/accessibility, backup/rollback, and physical-device checks.
- [ ] Measure hosted upload/inference/cold-start response times against manuscript requirements, including the recorded five-second target; fix failures before release.
- [ ] Cut over only after release gates pass. Keep credentials, student records/images, datasets, and private models outside Git.
- [ ] Update CHANGELOG.md each work session and keep KNOWLEDGE.md, PROJECT_PLAN.md, this checklist, and setup READMEs aligned with verified changes.
