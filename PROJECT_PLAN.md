2026-10-28 Vercel font-swap correction: reproduced live About font loading with1200ms delayed Manrope request: brand width99.75 before font versus106.89 after, both exposed by curtain opacity0. Added font preload and early bounded font-ready gate to all four HTML heads; curtain stays white until font loads, then fades in. At2200ms timeout the page fixes its fallback font for that document to prevent a later swap. CSS adds pending/fallback classes. Local delayed-font checks on all four pages confirmed cover1 before readiness, cover0 afterward, Manrope applied before reveal and stable subsequent text widths. Strict build passed. Timeout/failure and physical-device checks remain unverified; not committed/pushed yet.

2026-10-28 page handoff flash fix: user reported a quick glitch between supporting pages despite earlier settled-state checks. Confirmed live About-to-Data-use pagehide cleared outgoing curtain opacity to0 before departure. Updated landing src/page-transitions.ts to persist opacity1 before navigation and retain it during pagehide; pageshow restores cached pages. Comparison measured live departure0 versus local fixed departure1, with arrival0 and Back0 for both. Strict build passed. Earlier audit did not test this final outgoing state and missed the bug. Fix is local/unpublished; physical-device visual confirmation remains open.

2026-10-28 approved landing checkpoint: user accepted the visible content fades and requested commit/push. Includes page transitions, content-triggered section fades, local admin-link fallback and prior publication notes. Latest strict build and desktop/mobile browser checks passed as recorded below. Production rollout of this revision remains to be verified after push; APK/device/full application work remains open.

2026-10-28 visible section fade correction: user could not perceive edge fades. Landing motion.ts now triggers on each supporting section's content wrapper at88% viewport entry/12% exit, using a750ms interruptible opacity fade from0.08 to1. Hero retains its original intro. Focus-within CSS covers wrappers; reduced-motion clears their opacity. Build passed. Chromium1440/390 checks for all four wrappers measured0.08 before entry,0.60-0.67 during the fade and1 afterward; reduced-motion restored all to1. Local only; user review pending.

2026-10-28 homepage section fade trial: replaced separate group entrance fades in landing src/motion.ts with one stationary opacity surface per section, easing toward viewport-edge visibility over350ms. Sections become fully opaque in the reading area and fade on exit in either scroll direction; tall sections use edge distances. Existing hero intro and role/workflow selection feedback remain. CSS keeps keyboard-focused sections opaque; reduced motion restores all sections. Build passed. Chromium1440/390 checks measured all four supporting sections near0.45 opacity at entry and1 when aligned, and all five at1 after reduced motion; zero page errors. Physical-device and user visual review remain open; local/unpublished.

2026-10-28 correction: replaced skipped native document transitions with a white fixed curtain:280ms outgoing opacity and360ms CSS entrance, present in all four HTML documents before scripts. Lifecycle/timeout cleanup restores canceled navigation and Back. Local dev now supplies the documented public admin login when VITE_ADMIN_URL is blank; production keeps explicit configuration. Build passed. Chromium1440/390 checks observed active intermediate outgoing opacity on all three supporting routes, visible admin links, cleared curtains, Back and reduced-motion recovery, zero page errors. Live admin destination/physical devices untested; unpublished.

Landing publication2026-10-27: user authorized deployment. Separate Vercel project
graphiscan now serves https://graphiscan.vercel.app from main, root
graphiscan/landing-web. Production admin link configured; APK remains Coming soon.
Local production build and initial four-route public HTTP checks pass. Physical
device/APK and remaining overall requirements are still open.

Next-session direction2026-10-27: user is stopping after the landing-page session.
Landing work and tab titles are pushed to main through9afd123. On resume, return
to overall requirements and remaining project work; reconcile this plan with
CURRENT_REQUIREMENTS.md, WORK_CHECKLIST.md and verified system behavior before
choosing the next pending implementation. Do not assume more landing polishing.

Latest landing refinement2026-10-27: static supporting-page content groups, plain
home links and justified paragraphs implemented; restored prior Platform button
layout per user. Final build and18 pre-justification supporting-page browser checks
pass. User visual review and physical-device checks remain open.

Landing mobile/supporting-page refinement2026-10-27: readable copy, stable mobile
role switching/FAQ expansion, equal workflow cards, transparent smooth menu and
complete mobile copyright/link footer implemented. About/Data use reading layouts
and Download spacing/install cards refined. Build and focused four-route browser
checks pass at320/360/390/768/1440 widths. Physical-device/visual approval and
publication remain pending; existing core-app work remains deferred.

Landing motion repair2026-10-27: refresh flash and headline-offset regression
corrected; initial hero CSS entrance plus replayable GSAP fades retained. Platform
devices/role content use stable grouped fades. Build and isolated startup/reload/
replay/geometry/reduced-motion checks pass; user visual review remains pending.

Landing screenshot refinements 2026-10-27: desktop section alignment/viewport fit,
balanced Platform spacing, taller role phone and wider admin laptop implemented.
Role heading capitalized; rejected role-detail box removed. Build and four-size
browser section/all-role fit checks pass. Local visual review remains active.

Landing content 2026-10-27: replaced letter scene/screening note with sourced
dysgraphia information and native link underlines. Scene loader removed from
production. Build and three-width browser checks pass; user review pending.

Landing sizing 2026-10-27: resumed review; original hero retained. Four main
content sections now use full-width wrappers and minimum hero viewport height,
growing for content on phones. Download/footer unchanged. Build and four-width
browser checks pass. Local preview awaits user visual approval.

Landing checkpoint 2026-10-26: reference-led source rebuilt and locally verified.
Latest steering is implemented: preserve photographic hero, white later surfaces,
no diagonal arrows, close Discover underline, consistent section rhythm and device
mockups with a uniform graphite phone bezel. Download page simplified and checked.
Five-width homepage and three-width download checks, trace/fallback/reduced motion,
release fixtures, TypeScript and build pass. User visual review, physical phone,
signed APK/domain/QR/publication remain open. Existing core app work stays deferred.

Landing reference study 2026-10-26: supplied Linear/Apple/Samsung PH/Igloo plus
Lando are analyzed in .10k/reference-study.md. No application changes in this
study. Current landing design is still unapproved; next resolve the opening and
representative product composition with the user's full-screen/Three.js/GSAP
and responsive requirements. Earlier pending-reference notes are historical.

Current landing priority 2026-10-26: initial standalone landing-web source exists,
but visual direction is unapproved. User will supply liked websites; gather and
analyze those before further redesign. Requirements: professional, full-screen,
responsive, meaningful Three.js/GSAP, concise copy. landonorris.com establishes a
craft reference, not copying authorization. Latest full-screen build/typecheck
passes; fresh layout/motion checks remain pending. Existing app work stays deferred.

Current priority 2026-10-26: previous app/workflow work is deferred at the user's
request. Landing page is next, pending the user's Markdown brief. RESUME.md saves
the app checkpoint and outstanding workflow/device checks. No landing-page
implementation has started and no existing verification gate is newly complete.

Latest progress2026-10-24: approximately65% full-project estimate. PR#11 is merged,
all reviewed public source is committed/pushed and the user viewed the READY
admin preview. First MobileNetV2 Initial Screening has supplied browser evidence.
Next private image, expert assignment/review, parent release/denial and Follow-up;
then admin/onboarding/permissions/audit, Android/APK/physical device and release
checks. Three-class model work, historical data/images, real-use privacy and
paper/deck/diagrams remain open. No migration rerun or new theme work is required.
Older preparing/publication-pending paragraphs below are historical.

Current UI priority2026-10-24: admin website and login colors match Expo, colors
only. Three presentation files changed; admin build passes. User requests source
commit/publication for hosted preview review; automated browser approval is not
claimed. Expo code is unchanged from its saved checkpoint. Retain the successful
Initial Screening and resume image/expert/parent/Follow-up checks afterward.

Latest screening checkpoint2026-10-24: user supplied browser evidence of the
first MobileNetV2 Initial Screening, Normal49.19%/High Potential50.81%, expert
Pending. PR#10 is merged as cf58120;35 isolated upload/hosted/model tests pass.
Exact Render revision is unverified. Next: private image, expert assignment/review,
parent release/denial and Follow-up; full role/native release remains open.

Resume decision2026-10-24: test the hosted core workflow in a browser tab first,
using Choose image from the PC. Complete upload/review/parent/Follow-up checks
before creating the APK, then verify Android-specific and physical-device flows.
This sequence is agreed; the first result has supplied browser evidence and
the remaining role workflow is unverified.

Saved-session checkpoint2026-10-24: approximately65% of the full project. User
requested saving state to resume later; RESUME.md is the active handoff. Hosting
startup/private model fetch and visible choices are established, while actual
prediction and teacher/expert/parent/Follow-up flow remain unverified/deferred.
Latest mobile UI and documentation are being checkpointed locally, without push
or new deployment. Remaining gates include native/physical-device/APK, admin role
actions, historical-data/images, three-class evidence, privacy and paper/slides.

Results loading2026-10-24: local Results skeletons now adapt to measured list
height and fill the visible content area. TypeScript, five fictional browser
size/role/theme/motion cases and native loading-only light/dark-font1.3 captures
pass. Actual handwriting submission was deferred by the user; inference and full
role workflow remain unverified. This UI refinement is local/unpublished.
Continuation: Students/Children across hosted roles and legacy Students/progress
also fill loading viewports. Directory/upload/legacy search fields have minimal
icons and hints. TypeScript, four fictional browser role/loading/search cases and
native student-loading light/dark-font1.3 captures pass; native search capture is
unverified. These follow-up UI changes remain local/unpublished.

Model-host continuation2026-10-24: Linux numerical parity passed all3 models/all136
images, source PR#9 is merged and private fetch verified. User reported catalogue
publication SQL success. Supplied02:28:16UTC Render logs now confirm verified
models3 bundle, one-thread sync startup and Live after the manifest-key correction
and REQUIRE_MODELtrue instruction. Public health200/me401/models401 pass;
authenticated catalogue, actual inference and role workflow remain unverified.
api/MODEL_ACTIVATION.md is the active
settings/rollback handoff. Overall60-65%.

Earlier model-host continuation2026-10-24: Linux numerical parity passed all3 models/all136
images with zero class changes. Final single-cache/builtin-ResNet server passed
the actual512MiB/no-swap/no-network16MP noise probe at422.59MiB peak process RSS.
48 model/backend/write tests,12 Linux private-bundle tests and24 isolated catalogue
cutover/rollback checks pass. Six private artifact chunks/four files are uploaded
to the existing Supabase project. Hosted SQL, API configuration/deployment and the
full role workflow remain pending; no student data or original model pins changed.
Separate release worktree starts from main; UI changes remain local. Overall60-65%.

Model-host work2026-10-23: user authorized online screening next. Synthetic
Windows profiling of the pinned runtime reached799.12MiB resident with all3
models cached; warm inference0.405–0.808s. This is not Linux/hosted evidence.
FP32 LiteRT copies passed all136 images/all3 architectures with zero class changes
and max score error9.15e-6. Optional schema3 adapter/staging/lighter container are
implemented locally;47 model/backend/hosted/write tests passed. Windows resident
peak253.79MiB for the single-cache adapter and472.22MiB for fictional full API with
generated16MP images. Linux512MB fit, private provisioning, registry cutover and
deployment remain unverified. Original model pins/manifest/registry are unchanged.
Card preference unspecified; no paid service or secret upload. Overall60–65%.

Logout/loading2026-10-23: shared confirmation modal and feed skeleton coverage
implemented across native app source, including hosted/legacy data views and
query-scoped loading.14 fictional UI checks,18 mobile/19 shared tests, TypeScript
and1296-module Android export passed. Native dialog/Back check remains open;
user-reported working pages preceded this change. Source checkpoint e87bf07 is
saved locally; follow-up publication is pending. Overall60–65%.

Continuation2026-10-23: final11 fictional directory browser checks,18 mobile/
19 shared tests and TypeScript passed. Picker-theme recapture and directory
design extension are complete. Existing Android Studio now runs a new API36
GraphiScan_Pixel_6 emulator with Expo Go58.0.5; native login light/dark rendered.
New preview:android launcher resolves the observed IPv6 Metro/IPv4 adb mismatch.
Native login at dark font_scale1.3 fits. Android height keyboard avoidance fixed
covered password/sign-in controls and native recapture confirms their visibility.
Final TypeScript/Android export passed1295 modules. Expo Go configuration reload
can fail with EventEmitter startup error; fresh process recovers, cause unverified.
User confirmed private native hosted sign-in after a wait; role/workflow evidence
is separate. Original delay cause/timing was not captured.
Native role workflows, physical-device/APK and all model/data/privacy/paper gates
remain open; this is initial emulator evidence, not a native release. Overall60–65%.

Progress review2026-10-23: approximately60–65% of the full project, as an
engineering estimate rather than a measured task score. See the workstream
table in CURRENT_REQUIREMENTS.md. Current schema through021 is applied and the
last required hosted preflight passed38 checks; no new numbered migration is
prepared. Local Expo create/edit/filter source is implemented. Remaining work:
final UI/theme review and source publication; real hosted admin/onboarding/role/
Storage workflows; model-capable hosting and three-class evidence; historical
record/image reconciliation and rollback; Android device/APK checks; approved
privacy and final manuscript/deck/diagrams. This was a documentation/Git-status
review, with no new runtime checks or live mutations.

Continuation2026-10-23: hosted native student create/edit and server directory
filters are implemented and locally checked. Real hosted/device proof remains
open; a final native-picker theme recapture is pending. User now requested
Scrollcraft installation for website work: upstream skill installed/24 hashes
verified, available next turn. No new SQL, live record writes or publication.

Current Expo design2026-10-22: workspace/skeleton source is implemented locally;
latest logo-led login awaits user visual feedback after the full Dribbble comparison.
TypeScript/native Hermes export passed;29 fictional browser states fit, including
reduced-motion skeletons. Impeccable finish review requires Android recapture;
no device/APK/native approval yet. School grouping/filtering and student-creation
parity, model hosting, actual scoped role workflows and release evidence remain
open. No SQL020/021 rerun is needed. See newest CHANGELOG for exact evidence.
User checkpoint: finish this local design slice, save it and commit tomorrow.
No staging/commit/push/merge/deployment ran. Next session reviews the current UI,
checks PR#8 state and saves source through feat/expo-design-refinement. Native
device captures remain the Impeccable finish-review gate.

Expo source checkpoint2026-10-22: native app now defaults to the deployed HTTPS
v1 API; legacy requires explicit opt-in. AccountSetup provides branded password
and published-agreement gates. Role-aware Home/tabs, shared spacing/typography,
list/detail grouping and local sign-out feedback are implemented. Vue user-app
was read as the behavior reference and is unchanged. TypeScript and Android
Hermes export passed; fictional browser onboarding and teacher/expert/parent
layouts were inspected at390/320 with no horizontal overflow. This is not native
device or real Auth/consent verification. Android SDK exists, connected devices0;
no APK was generated. Next: review on Android, then hosted role/Storage/actions,
student-creation parity and model-capable screening. Privacy audience, historical
data and model/manuscript release gates remain open. SQL020/021 need no rerun.
Current publication checkpoint2026-10-22: PR#4 merged as b25d170; Researcher/Guest
role-choice removal is on main. Migrations020 and021 are applied; the last hosted
read-only preflight passed all38 checks. Assignment-access API/admin source is
being saved on feat/admin-assignment-access for a follow-up PR, not yet deployed.
607 contract/507 isolated SQL and77 focused Python checks plus admin build and
fictional responsive previews passed. Next: merge/deploy matching source, then
controlled authenticated hosted assignment checks. Earlier absent/pending SQL
and pause notes are historical; do not rerun migrations. Data/model/privacy/device/
manuscript and credential verification remain separate release gates.
# GraphiScan project plan and panel tracker

Latest migration slice2026-10-22: explicit assignment eligibility source is
implemented (scoped API, Edit dialog, atomic SQL/audit and020 preflight). Local
607 contract/506 isolated SQL/77 focused Python checks and responsive browser
preview/build passed. Hosted metadata confirms020 absent; installed schema019.
Next is020 owner execution and required read-only rollout check, matching API/
admin publication and actual scoped behavior. Historical data, credentials,
model, mobile and manuscript gates remain open. See `api/ASSIGNMENT_ACCESS.md`
under `graphiscan/` for the rollout and evidence boundaries.

Users role choices2026-10-22: Administrator, Teacher, Parent and Expert. User
requested removal of Researcher/Guest from selectable Users roles. Source/build/
fictional browser checks complete on `fix/admin-user-role-options`; publish via
the normal PR/Vercel flow. Existing accounts/history retain their stored roles.

## Current admin-first release — 2026-10-22

Presentation decision: desktop browser admin is primary; responsive layout is a
fallback. Expo is the native Android application; web exports/previews are
development aids, not its release target. Account dialog/table alignment source,
build and fictional Chromium review are complete; live reset/delete remains open.

Hosted verification started: actual fictional-account creation/edit/school
membership/disable/reactivate/removal passed. Reset/delete pending user private
issuer-password entry; audit/student/assignment walkthrough remains. Seventeen
isolated admin tests pass with updated optional-migration mocks. See latest
CHANGELOG/RESUME for the preserved active fixture and exact evidence.

Current requirements audit: [CURRENT_REQUIREMENTS.md](CURRENT_REQUIREMENTS.md) reconciles all35 existing project Markdown files and all16 panel commitments. Next: close the hosted admin lifecycle/assignment checks, then resume existing Expo integration, free model hosting and the full teacher/expert/parent workflow. No new tests or mutations ran for this audit.

Production handoff complete: PR#1 merged as `2ddb85f`; Render now follows main and its branch-change deployment succeeded/live. User confirmed hosted login/dashboard. Full account/Storage/model/mobile verification is separate. Blueprint/checkpoint edits are saved locally but not yet committed.

- User deferred Expo and requested admin completion, then deployment.
- Implemented source: account details/school/permission editing, disable/activate confirmation, reauthenticated temporary-password reset and unused-account deletion; existing dashboard, directory, results/progress, audit and settings flows retained.
- Database:017-019 installed; actual restricted read-only checker passed all33 checks after019. Do not rerun these migrations. No live reset/delete evidence yet.
- Evidence: both Vue builds pass, eight Python source files parse and production admin-only factory loads routes; fictional action dialogs reviewed at1440/390px. Actual Add user completion was confirmed earlier.
- Deployment: Render Free/Singapore API is Live at `https://graphiscan-admin-api.onrender.com`; Vercel admin is READY at `https://graphiscan-admin.vercel.app`. Private settings/CA uploaded; frontend-only upload inspected. Public login/health/exact-origin preflight return200; hosted login/dashboard is user-confirmed. PR#1 is merged and Render follows main. Hosted model inference remains disabled; no APK exists.

Older timeline checkpoints below are historical. Use `graphiscan/api/ADMIN_RELEASE.md` and the newest CHANGELOG entry for the active release scope.

Hosted Add user milestone (2026-10-22): user-created account confirmed by actual read-only reconciliation (1 Auth identity,1 app profile,0 Auth-only identities). Creation completion is observed after local API routing fix. Next: new account password/privacy gates in role-appropriate client, then live Edit/status behavior. Delete/password reset and deployment remain pending; source uncommitted.

Local account setup (2026-10-22):018 verified and user saved server Auth secret; account issuance service loads and local API5002 is running (health200, anonymous accounts401, admin5173 reachable). Remaining: private sign-in and authenticated Add user/Edit verification. No real account writes or deployment occurred; provider-key validity is not yet established.

Account rollout (2026-10-22): user applied018 and actual restricted read-only checker passed28 catalog/permission/session checks. Schema installation is through018. Remaining activation: private server Auth secret setup, API start/restart and live account-flow verification. No real account creation/deletion or deployment occurred. Do not rerun017/018.

Account management source update (2026-10-22): Add user UI/API and unapplied migration018 prepared with durable Auth issuance reservation, first-login password gate, optional memberships and no automatic grants. Edit recovery/navigation tightened. Admin build passed and fictional responsive dialog reviewed. Activation requires reviewed018, private server Auth secret and live backend verification; no SQL mutation tests or real account writes occurred. Delete/password reset remain pending. Installed schema remains through017; deployment paused.

Current admin refinement (2026-10-22): implemented shared control/dialog sizing and ordinary refresh-button presentation across hosted and legacy admin pages. Six hosted and five legacy refresh views inspected at1440/390px; both Vue builds passed. Changes remain local/uncommitted. Deployment and provider setup remain paused.

Latest budget direction (2026-10-22): model hosting must be free. Cloud Run provider selection is on hold while a suitable free host and account/card constraints are resolved. Portable Flask/model container packaging, stable pagination signatures and exact model-source byte preservation are prepared;35 focused Python checks and admin build passed. No container build/live deployment or APK exists. Save latest source on `deploy/free-hosting`; keep its Vercel auto-deployment disabled until a public API origin is ready. See `graphiscan/api/HOSTING.md`.

Current hosting direction (2026-10-22): follow the agreed `SYSTEM_DESIGN.md` stack: admin Vue/Vite on Vercel; Flask/Gunicorn and TensorFlow/Keras together on Google Cloud Run; Supabase PostgreSQL/Auth/private Storage; Expo/EAS Android builds. GitHub is the source repository. Vercel admin project creation/Git connection is prepared, but no code is staged/committed/pushed and no service is deployed. The provisional separate Vercel API project is not the selected backend host. Cloud Run access/billing/container/model provisioning, private server configuration, public API origins, hosted checks and mobile release remain pending.

## Supabase migration status (2026-10-21)

Latest017 rollout evidence (2026-10-21): user applied `017_account_management.sql`, privately configured the separate admin-writer connection, and the restricted read-only checker passed23 catalog/privilege/connection checks. No records were changed. No Flask listener was active on port5002 at verification time, so it will use the new setting when next started. Schema migrations are installed through017; MySQL data migration, reconciliation and application cutover are still open.

The target Supabase schema and staged v1 SQL migrations are installed through 016 in the disposable hosted project. The user applied the 016 setup bundle; an independent restricted read-only check passed all 14 catalog, grant, index, and zero-identity denial checks. The current Flask source is running on the local hosted API port; health is 200, unauthenticated account/audit reads are 401, and service logs show signed-in list requests returning 200. Do not rerun 016 or its grants. These checks do not establish full migration or cutover.

The repository has an opt-in Supabase/PostgreSQL v1 backend and a separate MySQL legacy app. Source now also includes administrator/researcher account updates through `PATCH /api/v1/accounts/{user_id}` and an isolated, locally verified migration 017. Migration 017 is NOT applied to Supabase; 016 remains the latest installed hosted migration. Account issuance and password reset, hosted 017 rollout, real authenticated role workflows, MySQL record/image migration and reconciliation, final model evaluation/three-class decisions, retirement/cutover of legacy routes, and release verification remain open. Some required steps depend on private hosting access, approved manuscript/privacy artifacts, the real dataset, and a physical Android device. Keep those dependencies distinct from code that can be completed locally.

Reference UI iteration (2026-10-21): hosted admin pages now use white page surfaces, white cards and light borders, with shared page insets, section gaps, card padding and control spacing. Sidebar and heading alignment are consistent and filler is trimmed; no brand underline/profile. Login is full-tab42/58 without margins, centered intro/note and complete laptop preview. Dashboard chart/table/review panels use loaded data and align in rows. Admin build passed; fresh visual review after the spacing adjustment remains open, followed by deployment readiness. No backend/model/permission changes in this UI pass. Existing016 setup is verified and must not be repeated.

SQL step verified (2026-10-21): user applied016 bundle; all14 independent restricted hosted checks passed. Existing fictional test admin now has the two read grants. Current API5002 restarted and new anonymous routes return401; fresh signed-in populated list display pending. Do not rerun migration/grants. Continue reference-based UI work after confirmation, then deployment readiness; account actions and complete role workflows remain open.

Current order (2026-10-21 user steering): install/verify missing 016 via prepared `016_admin_reads_setup.sql` (existing test admin read grants included), restart hosted API source and check populated account/audit reads; then clearly apply supplied dashboard references across admin UI; then prepare admin deployment. Live read-only check confirms 016 absent and old API routes404; no installation/grants/deployment performed by agent. 146 isolated SQL/setup checks passed. Previous subtle UI pass was rejected by user and is not visually approved. Account mutations and broader hosted workflows remain separate unfinished features.

Admin UI/read checkpoint (2026-10-21): management, screening and system pages now use a common page grid and Inter scale. Users/Audit have read-only lists in source via new v1 routes and unapplied migration 016 with separate global permissions; account creation/edit/disable remains open. User-supplied dashboard references informed a denser hosted dashboard with compact metrics and a recent-results table. Admin build, isolated endpoint/SQL/contract tests and synthetic six-width page/browser checks passed. Hosted migration/grants, live populated data and real end-to-end screening/review/release remain open; do not count isolated fixtures as deployment.

Admin pages checkpoint (2026-10-21): original eight hosted sidebar choices and responsive page states implemented. Dashboard, Students/Schools, Results, Progress history and Settings password flow are connected to current v1 capabilities; Users and Audit Logs have consistent unavailable screens while their scoped hosted APIs and account actions remain planned. Progress reads recorded history only. Admin/user builds, 53 synthetic six-width page checks, 16 screening checks and dashboard/modal regressions passed; no real provider writes or populated workflow tested. Next: design/implement scoped hosted account and audit endpoints before claiming full management parity; real upload → assignment → review → release remains pending.

Clarified palette and original-page references (2026-10-21): user clarified3-color limit applies to theme/background surfaces, not functional actions/status colors. Original dashboard, management, screening and forms are the authoritative visual references throughout admin. Restored red logout/signout and green/amber/red review/classification colors in hosted dashboard and older dashboard. Hosted Students/Schools now use original-style record tables, toolbars/filters, loaded-count summaries and native modal editors via opt-in adminPresentation in shared HostedDirectory; user app default presentation retained. HostedScreenings now uses original-style desktop table/phone record cards, loaded review counts, badges and primary assignment save styling. Native editors preserve validation/uncertain-save guards, show errors within dialog, block unsafe Escape dismissal, lock background scroll and retain signout during unresolved saves. Updated HostedAdminWorkspace.vue, HostedScreenings.vue, HostedAccess.vue, shared HostedDirectory.vue, AdminDashboard.vue, style.css, README and dashboard browser fixture. Final admin/user builds passed;16 existing intercepted screening checks passed after table conversion; final six-size dashboard/management/screening checks passed, including student/school modal focus/open/close, unknown labels, refresh error/retry, visible modal errors, uncertain-save Escape protection/signout and normal logout. Desktop/phone table/form screenshots inspected; final phone modal screenshot is viewport-only. No real writes, Auth/backend/model/API changes. Users/Progress/Audit Logs hosted feature migration and real populated workflow remain pending; their original pages remain the reference.


Hosted dashboard now follows original admin reference (2026-10-21): user clarified older dashboard is visual reference and actual post-login workspace must match. Added HostedAdminWorkspace.vue, shown through optional shared HostedAccess workspace slot after ready. Reuses AdminLayout blue sidebar/mobile drawer, summary cards, review bars, result ring and recent screenings; Students/Schools/Results/Account buttons keep existing hosted directory/results mounted. Summary snapshots come from already-loaded scoped/filtered lists; counts explicitly labelled loaded, never global totals; exact classification labels retained. Recent rows open existing detail/assignment controls. Added optional custom navigation/signout to AdminLayout without changing legacy defaults; pending-directory navigation block forwarded to shared route guard and local navigation. Hosted API/session isolation retained; no legacy credential bridge, new endpoints or provider writes. Updated admin wrapper/README, shared directory snapshot/exposed refresh/tab methods, screenings snapshot/detail methods, workflow fixture and new check_hosted_dashboard_browser.js. Final admin and user Vue builds passed.16 intercepted screening/workspace checks passed; six-size dashboard checks1440/1280/1024/768/390/320 passed counts, sections, unknown category preservation, load failure/retry and hosted logout; final desktop/phone screenshots inspected. Active sidebar style corrected and screenshots wait for drawer transition. This supersedes earlier note that hosted dashboard visuals are pending. Users/Progress/Audit Logs hosted feature parity and real populated end-to-end workflow remain pending.


Hosted signed-in route fix (2026-10-21): user observed URL stayed /login after sign-in. Shared HostedAccess.vue now emits non-sensitive ready-state changes; admin wrapper reconciles ready sessions to /workspace and non-ready/signed-out state to /login. Router uses two records with the same component to preserve the in-memory hosted client; an alias was rejected during browser verification because Vue treats alias navigation as duplicate. No token persistence or legacy bridge added; onboarding stays /login and direct sessionless /workspace returns /login. Admin README and check_hosted_admin_browser.js updated. Both Vue builds passed before final route-record correction; final admin build passed after it. All15 intercepted hosted browser checks passed including sessionless entry, ready-route/session continuity, screening/assignment conflict flows and signout return. No real provider writes. Legacy dashboard visual work remains separate; hosted dashboard parity is still pending.


Admin dashboard visual pass (2026-10-21): refined existing /admin/dashboard in AdminDashboard.vue using Inter,28px title,18px section headings, aligned24px panel spacing,12px panels,8px flat controls and44px actions. Charts/legends/recent status badges use labelled blue/ink palette with white/tints; classification/review calculations and requests unchanged. AdminLayout wordmark now GraphiScan; style.css sidebar links and logout use consistent8px corners/14px text and neutral logout treatment. Final admin build and six synthetic browser sizes1440/1280/1024/768/390/320 passed fit, refresh, menu Escape/focus restoration, empty/error-retry and recent result destination checks; no page errors. Desktop/phone screenshots inspected, final phone alignment/row-spacing correction confirmed. No real data, Auth changes or writes. IMPORTANT: this dashboard is still the legacy /admin/dashboard route; canonical hosted /login records workspace remains separate, dashboard parity/migration is NOT implemented. Next: remaining admin page consistency and hosted populated workflow.


Responsive admin login refinement (2026-10-21): user approved tightening layout and improving responsiveness. Form now max380px (was340), logo64px (was56), clearer28px heading/14px labels,50px inputs/48px submit; retained upper-left branding, flat button and16px field text. Shell height adapts to viewport; tablet collapses to single-column at980px, phone padding corrected and short-laptop/landscape rules added. Preview reduced to560-700px and tilt12deg so more dashboard is visible. Password placeholder shortened for320px. Final admin build passed; nine browser sizes1920/1440/1366/1024/980/768/390/320/844-landscape passed horizontal fit, brand/form separation, empty inputs, stable focus size,44px controls and reachable submit;1366x768 fits vertically, landscape scrolls naturally. Screenshots inspected, final320px confirmed. No Auth/backend/mobile changes.


Reference-based admin login (2026-10-21): user supplied three modern references. Used blue product-preview reference as main direction with compact340px left form, restrained26px heading,48px fields, aligned brand, white large shell and grey outer surface. Right panel now has smaller original headline/description plus angled CSS device showing local synthetic empty-dashboard capture; removed monitoring glass card/initials. Added admin-web/src/assets/admin-workspace-preview.png and provenance README; no private records/reference artwork copied. Final admin build passed;15 intercepted entry/role/redirect checks passed.1440/1024/390px layouts fit, image decodes, inputs empty; final desktop brand/form offset0px and screenshot inspected. No new Auth/signup/social/remember features or mobile/backend changes. User may review at /login; original /access redirect remains.


Admin form rebuilt; awaiting user visual references (2026-10-21): added AdminSignInForm.vue with400px centered form, Welcome back title,52px icon fields, inline accessible eye toggle, nearby errors and flat primary action. Shared HostedAccess now offers an optional sign-in slot backed by the same reactive email/password state and existing login/password/privacy/role logic; default user form remains available. Retained approved large box/right panel. User then requested removing Admin web panel label, account-issued helper and black button shadow: removed both texts and explicitly set button appearance/box-shadow none with solid border. Both Vue builds passed;15 entry/role/redirect checks and12 hosted workflow checks passed before final text-only removals; desktop/phone focus checks confirmed stable16px text/52px fields and password-toggle behavior. Final browser check confirmed absent texts, no shadow, flat appearance and empty fields. No credentials/provider writes. Next wait for user preferred pictures before further aesthetic changes.


Single main admin entry (2026-10-21): user was confused by Admin Web Panel versus workspace. Canonical admin /login now serves hosted admin/researcher flow; / and /access redirect there. No visible workspace-switch links. Old MySQL login is explicitly /legacy-login, with old /admin/* guards, API401 redirects, logout/password-success redirects, tools and old Flask admin-login return updated accordingly. Hosted sessions are never bridged to legacy tokens. Shared component adds default-preserving display props; Vue user and Expo role allowlists unchanged (teacher/expert/parent). Both Vue builds,15 intercepted entry/role/redirect/isolation checks and12 existing hosted workflow checks passed; no real credentials/provider writes. Flask redirect source changed but legacy server behavior not runtime-tested/restarted. Modern reference review: official shadcn login/signup and Clerk sign-in; inspected shadcn two-column login visually. Reference-inspired visual changes beyond existing design are recommendations only; retain approved blue panel/wording. Updated admin README. Next remains admin UI refinement, then first hosted teacher upload/review/release.


Admin design restoration (2026-10-21): user clarified that removing AI slop should not strip the original panel design/wording and approved restoration. Restored original GRAPHISCAN label, Handwriting Screening and Progress heading, original description, gradient/circles, Admin Monitoring card and T/P/E initials in shared AdminLoginPanel.vue/style.css for both admin sign-ins. Retained max1280px/min760px desktop sizing, responsive collapse and explicit16px input fixes. Admin build and six intercepted login layout/toggle/error/retry cases passed at1440/768/390px; restored desktop screenshot inspected. Preview cleanup now leaves both inputs empty and removes mock routes. No real sign-in, Auth/backend/mobile changes. Preserve this design going forward; refine rather than strip it.


Web-first admin preference (2026-10-21): user clarified admin is primarily desktop web, with responsive sizing for flexibility; user app must not offer admin access. Enlarged both admin sign-in containers from1120x700 to max1280px/min760px on desktop; retained phone collapse. Replaced decorative gradient/shapes/floating card/avatar initials with plain blue panel and concise task copy; removed unused corresponding CSS. Existing web sign-in links retained pending clarification whether both options means Admin/User or existing/new workspace. Source inspection confirms hosted Expo restricts roles to teacher/expert/parent and Vue user wrapper has the same allowlist, with no admin option added. Admin build and six intercepted login checks passed; desktop/phone screenshots inspected; no Auth/backend/mobile changes.


Admin login refinement (2026-10-21): reviewed original admin/user Vue Login.vue before revising the previous generic hosted form. Extracted original admin blue panel into admin-web/src/components/AdminLoginPanel.vue and reused it in both admin /login and /access. Refined proportions, spacing, input borders, buttons and phone collapse while retaining issued-account sign-in behavior. Shared HostedAccess adds only an optional welcome slot; Vue user wrapper does not supply it. Both Vue production builds passed; six intercepted login cases across1440/768/390px passed fit/password-toggle/error/retry checks, and12 existing hosted workflow checks passed. Screenshots inspected; no real credentials or provider writes. Public signup remains absent. UI remains current priority; populated screening workflow still pending.


Admin UI priority (2026-10-21): user chose admin first and requested the same design with better consistency. Implemented admin-only hosted styling in admin-web/src/views/HostedAccess.vue matching the existing blue/white Inter identity; shared user components unchanged. Added control tokens and consistent page titles, primary/secondary buttons, form borders/radii and filter heights in admin-web/src/style.css. Final admin build passed; 12 existing all-intercepted hosted browser checks passed. Seven legacy admin pages checked at1440/390px with synthetic empty responses:14 fitting layouts, matched heading scale, no page exceptions; Add User dialog open/Escape and hosted password toggle checked. Desktop/mobile screenshots inspected. This is visual/mock verification, not live legacy data or new hosted writes. UI is the current priority; first hosted teacher upload/assignment/review/parent-release remains pending. Keep current identity; no mobile changes requested.


Role onboarding checkpoint (2026-10-21): user confirmed expert workspace working and parent onboarding/student check done after role-specific password/notice instructions. These are user-reported outcomes, not independent inspection of password/acceptance records. Teacher synthetic student visibility was also user-confirmed. Next: first hosted teacher upload using generated test PNG, then admin expert assignment, expert review and parent release checks. Generated ignored output/playwright/synthetic-workflow-test.png (256x256 white fixture) for transport/inference testing only; its classification has no handwriting-quality meaning. No upload/review/release has yet been verified.


Teacher checkpoint (2026-10-21): user confirmed the synthetic student appears after the teacher onboarding instructions. This is user-reported teacher directory success; password/notice steps were not independently inspected. Next: sign out and onboard graphiscan.expert.test@example.invalid with its private temporary password, change password, sign in again and explicitly accept the current workflow notice. Expert may have no assigned screenings until the later teacher upload/admin assignment. Then onboard parent. Populated upload/review/release remains unverified; no migrations/setup/XAMPP repeats.


## Active direction after user clarification, 2026-10-20

User requested save/continue later(2026-10-20). Checkpoint saved in RESUME.md; overall56%. Resume with teacher onboarding on hosted Expo http://localhost:5174 (not yet done), then expert/parent and populated upload/review/release. Admin onboarding user-confirmed/API request200 supported;01523-check preflight passed. Services left as-is; check liveness rather than blindly restarting. No setup/SQL/password repeats or XAMPP repair.

Latest client checkpoint(2026-10-20): admin sign-in/newnotice/synthetic directory success user-reported. Hosted Expo web ready at http://localhost:5174(session77508; explicit hosted mode→API5002); root200/bundle/browser login/CORS verified without credentials. Next teacher password+notice+student check, then expert/parent onboarding, upload/assignment/review/parent release. Overall56%. No migration/setup/XAMPP repeat.

Latest applied015 checkpoint(2026-10-20): user reports atomic success; all23 agent-run restricted read-only setup checks passed. Updated hosted API5002(session43462) health200/admin/access200/protected anonymous401. No SQL/credential/setup repeats. Next fresh admin sign-in/newnotice acceptance/synthetic directory check, then hosted Expo per-role password/privacy onboarding and populated upload→assignment→review→parent release. No authenticated populated/device/write/deployment proof yet. Overall56%; XAMPP repair stays stopped.

Latest implementation(2026-10-20):3 Auth users user-reported created; bounded multi-account test-notice gates and atomic UNAPPLIED015_workflow_fixtures.sql prepared. Apply only that1 bundle once:3 forced-change profiles/1 synthetic school+student/school-scoped admin assignment grant/2 memberships/4 eligibility links/new4-ID notice, retaining old notice history/admin password.162 v1 tests/114 isolated SQL assertions passed; read-only checker prepared. Next owner application→read-only verification→hosted5002 restart→individual password+notice onboarding→upload/assignment/review/parent release. No live setup/role-flow proof. Overall55%, XAMPP repair stopped.

Latest steering(2026-10-20): stop unnecessary XAMPP repair. Hosted Supabase workflow has no XAMPP dependency; proceed with selected fictional hosted role/audience setup. Legacy MySQL files preserved/hash-verified offline, but accounts/students NOT deleted and no SQL restore verified. Do not resume privilege-table repair just to perform legacy cleanup without new user instruction. Overall53%.

User selected proposed fictional role setup and authorized old legacy demo-account cleanup (2026-10-20), preserving hosted admin/new fixtures/models/audit evidence. Cleanup is NOT implemented: MySQL read-only inventory failed2003 then2013 after hidden XAMPP startup; no usable SQL/backup/deletion. Next restore connection, verify backup and exact legacy demo/dependency scope before authorized removal. Proposed hosted role/audience package still needs implementation/tests; original notice must remain scoped. Overall53%.

Next-role-flow preparation (2026-10-20): concrete proposed fixtures/school-scoped grants and a separate draft notice are in `graphiscan/api/FICTIONAL_WORKFLOW_SETUP.md` and `fictional-workflow-notice.draft.txt`. No account/grant/notice/record writes or new SQL. User fixture choice pending. Existing single-account notice requires a bounded multi-account audience extension before the proposed four-role test; implementation/test/review remain planned. Existing notice must not be unscoped. Overall stays53%; this documentation is not populated hosted verification.

Hosted Vue admin screening list/detail/expert assignment UI is implemented at `/access` (2026-10-20). Includes scoped pagination/status/grade filters, private blob image, recorded model/report/review fields and current-school eligible expert choices. Revision failures require reload; no write replay. Both Vue builds/17 shared-client tests and fictional intercepted Chromium workflow checks passed, including narrow layout. No real hosted assignment/provider writes, migrations, accounts/grants or notice expansion. Overall rough53%. Next: explicit issued-role/notice/school/eligibility prerequisites, then populated upload/review/parent release and native/device/deployment checks. Legacy Vue/MySQL routes remain active as before.

Latest verified setup: user-run catalogue all12 checks passed, including3 model versions and MobileNetV2 default. Agent-run synthetic private Storage put/get/public-denial/delete all5 passed, no application database/screening writes. Overall rough51%. Next coding gap is hosted Vue admin screening/detail/expert-assignment UI. Actual populated upload/review/parent release still needs issued role accounts/current scoped eligibility and appropriate notice, followed by native/device/deployment checks. Do not repeat successful SQL/credential setup or broaden the admin-only notice.

Publication checkpoint: owner reported model SQL success; updated local API5002 session40531 activated. Factory check confirms3 pinned models and Storage configured. Interactive tools/check_v1_model_catalogue.py is prepared/compiled for fixed fictional-admin current Auth sign-in, protected metadata/default verification and temporary session cleanup. Actual hosted catalogue rows/default are not independently verified yet. No repeated SQL/restart needed; overall49%.

Latest implementation: three evaluated hosted binary versions staged with schema-v2 hash/source pins and isolated runtime caches. Explicit/default selections connect through existing React catalogue controls and authoritative reservation. Prepared UNAPPLIED graphiscan/db/postgres/publish_binary_models.sql publishes measured image-split metadata/3versions/MobileNetV2 default; no accounts/permissions/records changed.160 API regressions, expanded18 upload tests,11 isolated publication assertions and real synthetic inference of all3 pinned files passed. Next: owner runs only publication SQL, API restart and authenticated populated flows. Rough overall49%; this is local integration, not deployment or three-class completion.

Model evidence update: supplied training_results reviewed; active ResNet50 artifact match verified. Agent reran all3 binary models on136 test images through hosted preprocessing at0.50/0.75. At current0.75, MobileNetV2 leads85.2941%accuracy versus72.7941% each for ResNet50/EfficientNetB0. Full evidence/limitations in graphiscan/api/MODEL_EVIDENCE.md. Historical CSV cannot supply hosted accuracy/default because its path/rule differ. No model/threshold/registry/default changed; versioned multi-artifact support/publication, populated hosted tests and planned three-class comparison remain open. Rough overall47%.

Storage update: hidden-prompt settings saved; real S3 bucket metadata and bounded listing checks passed without writes/private output. Bucket privacy and object write/read/delete remain unverified. Model evidence/manifest/publication is next; API restart required after configuration before upload checks. Overall rough46%; earlier absent-Storage notes superseded.

Latest checkpoint: user reported atomic 013+014 applied; all 19 hosted read-only metadata/privilege/zero-identity checks passed. Updated local API5002 session32790 serves health200 and six new protected route probes401/no-store. No application writes or deployment. Storage settings and model manifest are absent; private bucket/hidden local S3 setup and reviewed evaluation/model publication are next, followed by issued-role access and populated end-to-end checks. Rough overall45%. Do not repeat the bundle; earlier unapplied/restart instructions below are superseded.

Latest local slice: upload/review/expert-assignment/model/request/image endpoints and React hosted actions are implemented behind prepared **unapplied atomic 013+014 bundle**. Apply only graphiscan/db/postgres/013_014_screening_writes.sql once, then restricted preflight and API restart. Uploads pin approved metadata, reserve requests durably, normalize images, use private S3 and lock students for atomic Initial/Follow-up completion. Review/assignment revisions and safe retries are checked. Cleanup/abandoned-work reconciliation is implemented. Tests/exports pass, but real Storage/model setup, evaluated registry publication, issued-role privacy/accounts, hosted populated/device flows, admin assignment UI and deployment remain pending. No fabricated evaluation/default or privilege seeds. Rough overall45% supersedes earlier estimates. See graphiscan/api/SCREENING_WRITES.md.

Latest verification: 012 is user-reported applied; all 22 independent hosted read-only metadata/privilege/zero-identity checks passed. Updated API5002 session54308 serves health200 and four protected reads401/no-store without authentication. No application writes or repeated setup. Authenticated populated/device/write workflows remain pending; estimate41%. Following pending-012 instructions are implementation history, superseded by this verification.

Latest slice: hosted screening list/detail/history/report reads and React hosted Auth/onboarding/read integration are implemented locally. Migration **012 is prepared but not applied**; apply only it once, then verify metadata/zero-identity denial and restart updated API. Twenty of 33 operations are foundation. Scoped SQL and build checks pass; authenticated hosted/device flows and write parity remain pending. Rough full-scope progress 41% supersedes the older estimate below. See graphiscan/api/SCREENING_READS.md.

Reuse the existing Vue admin and convert the existing user app to React Native/Expo. Continue through panel requirements, Supabase integration/migration and deployment; earlier time ranges are estimates, not a user-approved scope limit. Guest/demo work stays excluded.

- Implemented first conversion pass in graphiscan/mobile-app: current role navigation, existing-API login/recovery, teacher students/uploads, result/history, expert review and image viewing/sharing. Existing Vue user app remains as the parity reference.
- Connected recorded Initial/Follow-up labels through all nine existing role read APIs into React results/detail/history; isolated scope/provenance tests passed. Missing/conflicting labels are unknown, never inferred from visible order. This does not complete concurrent upload assignment or the hosted screening endpoints.
- Fixed the dictionary-row count access that could stop API and legacy Flask uploads before report insertion. Seven isolated Python tests cover the read slice and mocked upload/count paths; live upload and concurrency checks remain pending.
- Verified TypeScript, focused API/session tests and web/Android JavaScript export. Pending: authenticated React flows and physical Android checks, report/history parity, final launcher branding and dependency advisory triage.
- Next integration: reuse hosted Auth/password/privacy and directory capabilities in the converted user app and existing admin, complete hosted screening/review/release/report endpoints, explicit account issuance, controlled data migration/private image storage, then deploy and verify the complete flows. Do not pass Supabase UUIDs/tokens into the legacy /api/user adapter.
- Overall rough estimate: 38%; no deployment or complete Supabase cutover claimed.

## Historical proposed timeline requested 2026-10-20 (superseded as an implementation priority)

Planning estimate only, not a delivery commitment or implemented work. At 09:52
Asia/Manila, roughly 4–5 hours remain before the user's 14:00–15:00 target.
Overall progress is still approximately 35%, a rough full-scope judgment.

| Proposed local time today | Work target |
| --- | --- |
| 10:00–11:15 | Account issuance/explicit permissions and controlled fictional-role setup; required provider access can affect timing |
| 11:15–12:30 | Verify populated school/student creation, editing, assignment and denial paths |
| 12:30–14:00 | Begin protected screening upload/model wiring after preceding checks; complete only what passes verification |
| 14:00–15:00 | Verify completed scope and fix failures; do not label unfinished flows complete |

Realistic afternoon target is verified account/school/student work, with screening
integration dependent on earlier work. The full revised system is not a credible
14:00–15:00 commitment. Rough full-scope planning range: 2–4 focused working weeks
after required model artifacts/evidence, provider access, policy inputs, manuscript/
deck and Android device are available. This includes screening/private images,
expert/parent/report/history flows, model validation/selection, Expo parity,
migration/hosting and release checks; external delays can extend it. Guest-demo
work stays excluded from the active implementation priority.

Latest directory verification (2026-10-20): user reported no error after Refresh lists; API67766 confirms authenticated school and student GETs both returned HTTP200 at 09:50:19. Earlier school503 did not recur; root cause was not captured, so safe diagnostics remain without claiming a DB/permission repair. Scoped read success does not establish populated fixtures or write flows. No DB/grant/account/credential change or repeated tests. Next planned: account issuance/explicit permissions and controlled fictional populated-write verification, then screening/review/release. No automatic privilege grants; no need to repeat refresh/setup absent new failure. Rough full-scope progress stays 35%. Earlier active-error notes below are historical.


Directory retry evidence (2026-10-20): user applied filters and reported no students; authenticated /students?limit=25 returned HTTP200 in API67766 logs, confirming successful empty scoped student view. Earlier /schools503 still needs authenticated retry. Added persistent Refresh lists so both resources can be retried even after successful student filtering clears the shared error; both Vue builds passed. Next: user clicks Refresh lists, inspect API67766. No database/grant/credential change or claimed root cause; overall estimate stays 35%.


Active directory defect (2026-10-20): user sees Account setup complete and Students/Schools, but authenticated /schools returned 503. This is not a confirmed empty result. Diagnostic API5002 session 67766 now logs SQLSTATE only; user was asked to retry records so the failure code can be traced. UI now distinguishes not-loaded/empty and loads lists independently. Eleven directory tests and both Vue builds passed; valid-user fetch/root cause remain unresolved. JIT was already disabled, so no JIT change was made. Fix this before new features. No DB/grant/credential changes; rough progress stays 35%. Older successful metadata/zero-identity checks are narrower evidence.


Latest assignment setup checkpoint (2026-10-20): 011 is user-reported applied and all ten independent hosted read-only metadata/zero-identity checks passed. No writes, credentials, grants or records changed. Updated API5002 is running (session 99903): live health 200, unauthenticated options 401 and admin /access 200. Next: user signs in with the existing fictional Auth account/current password and confirms Students/Schools sections. Empty scope can be correct; no automatic management grant or populated-write evidence is implied. Overall rough progress remains 35%. Older installation-pending notes below are historical; do not repeat SQL/password/seed setup.


Latest workspace/options slice (2026-10-20): both /access ready states now include shared school/student lists, filters, details and forms, eligible teacher/parent selectors, revision recovery and explicit same-payload student creation retry. New assignment-options read route is local; UNAPPLIED 011 adds only an existing-reader fixed-path definer read capability, no data/grants/credentials. 156 Python/11 JavaScript/494 contract/284 isolated SQL checks and both Vue builds passed. Vite pages/modules returned 200; browser inventory was empty, so visual/live authorized form checks remain unverified. Next: apply only 011 once, verify hosted function metadata/zero-identity denial, restart API5002 and user-check Students/Schools sections. No automatic privilege seed or data migration. Rough overall progress is 35%; earlier checkpoints below are historical. See graphiscan/api/WORKSPACE_DIRECTORY.md.


Latest hosted mutation checkpoint (2026-10-20): 010 is user-reported applied. All 26 hosted metadata/invalid-session checks passed. Metadata was read-only; row-locking zero-identity writer probes were explicitly rolled back, with no application writes committed or private data/key output. Updated API5002 (session 6207) passed live health 200, four unauthenticated write routes 401 and PATCH/Idempotency-Key preflight. Authorized hosted writes/retries/concurrency and resource UI remain pending. Next: eligible assignment choices and school/student screens. No repeat SQL/password/seed setup. Rough overall progress remains 34%; older installation-pending notes below are historical.


Latest directory mutation slice (2026-10-20): school/student POST/PATCH are implemented locally with scoped assignment checks, profile/record locks, optimistic revisions, private duplicate warnings and durable HMAC-bound student creation retries. Unapplied 010 reuses the existing function-only writer, initializes a private random request-digest key and adds no application records/grants or new credentials. 151 Python/494 contract/265 isolated SQL checks passed; OpenAPI has fifteen foundation operations of 33. Next: apply only 010 once, inspect hosted permissions/zero-identity denial and restart API5002. Actual hosted writes/concurrency, assignment-option queries and resource UI remain pending. Rough overall progress is 34%; older checkpoints below are historical.


Latest hosted directory checkpoint (2026-10-20): 009 is user-reported applied. All 15 independent read-only function security/grant/zero-identity checks passed; no hosted writes or private record output. Updated API5002 is running: live health 200, three directory routes 401 without bearer after stopping superseded GraphiScan Python processes. Authenticated hosted record/scope requests and record UI/writes remain separate work. Do not repeat migrations/password/seed setup. Rough overall progress remains 33%. Older installation-pending notes below are historical.


**Current directory slice (2026-10-20):** Three school/student read operations
are implemented with current database-enforced session/onboarding/record scope
and signed keyset pagination. 140 Python/494 contract/210 SQL checks passed.
Unapplied 009 grants only the existing reader a restricted definer function;
no new credentials, writes, seed, frontend or hosted resource test occurred.
Next: owner-run 009 once, inspect hosted metadata, restart API5002 and verify
scoped reads. Then implement controlled record writes/UI and screening flows.
Full-scope estimate is approximately **33%**; older checkpoints below are history.
See [directory setup](graphiscan/api/DIRECTORY_ACCESS.md).

Hosted 008 update (2026-10-20): user reported migration success; independent read-only catalog inspection passed all seven logout-function security/grant checks. No hosted writes or function invocation occurred. Do not repeat setup. User confirmed admin browser sign-in displayed Account setup complete and sign-out returned to the sign-in form without error. This is user-reported evidence; hosted refresh/revoked-token replay and independent visual checks remain separate. Next implementation is authorized school/student resource access before screening/review/parent-release migration. Overall progress remains approximately 32%.


This combines the implementation sequence with the defense action tracker. Status is based on documented evidence; source edits alone do not prove runtime behavior.

See [WORK_CHECKLIST.md](WORK_CHECKLIST.md) for the consolidated implementation and verification checklist reviewed on 2026-10-17.

## Work sequence

**Shared sessions/client onboarding locally implemented (2026-10-20):** Login/refresh/durable-local-sign-out API plus shared Vue `/access` password/privacy/readiness flow are implemented. 129 Python/seven JS-client/494 contract/165 SQL checks and both builds passed. Actual hosted UI/session verification waits for user-run 008; no new password is needed. Hosted local origin is 5002; existing resource clients remain on original 5000 and are not migrated by this slice. Full-scope planning estimate is about32%, with percentages requested in every update; this is approximate, not measured readiness. See [session integration](graphiscan/api/SESSION_INTEGRATION.md).

**Core-scope steering (2026-10-20):** User asked to stop focusing on the demo and is planning to remove it. Stop guest/sample-demo rehearsal now; actual UI/API/role removal is planned only. Guest demo is optional in the design and absent from the supplied panel requirements. Focus on core admin/authorized researcher, teacher, expert and parent behavior, shared authentication/client onboarding, school/grade grouping, screening/model evidence, expert release and Initial/Follow-up history. Broader API/native/document requirements remain. Existing page-load checks do not replace that implementation work.

**Existing-role rehearsal and guest route fix (2026-10-20):** User reported admin/teacher/expert/parent views work; parent populated-result availability was not separately established. Fixed two guest dashboard cards to registered `/guest/demo` and rebuilt successfully. Next is fresh guest inference with a synthetic sample, separate from page loads or model evaluation; no official student result/validation writes are needed for that demo. Full hosted/native rebuild scope is unchanged.

**Hosted privacy lifecycle passed (2026-10-20):** User supplied all nine passing interactive checks: exact test notice, explicit acceptance, stable timestamp, stale-version denial, bootstrap/gate readiness and cleanup. No credentials saved/shared or password change. Temporary fictional onboarding is user-run verified; no client/resource access is implied. Next focus is the existing-app presentation baseline/rehearsal; both Vue builds freshly passed. Full rebuild requirements remain open and are not removed for the afternoon demo.

**Presentation target (2026-10-20):** User wants a progress percentage and a presentation approximately 2-3 PM today, Asia/Manila. [PRESENTATION_READINESS.md](PRESENTATION_READINESS.md) separates the rough full-rebuild planning estimate (25-35%, about 30%) from the existing prototype's un-rehearsed current demo readiness. Proposed immediate focus is a reliable existing-stack demonstration plus verified hosted progress; awaiting presentation-scope clarification, not removing full project requirements.

**Hosted test notice published and verified (2026-10-20):** User reported seed success/repeat error; agent read-only inspection passed eight publication/function flags, including canonical scoped current notice and no acceptance yet. Saved state is correct; no repeat/repair/password change is needed. Next: explicit interactive privacy checker. Actual acceptance, hosted concurrency and client onboarding remain pending; no agent-hosted mutation occurred.

**Hosted 007 reported applied (2026-10-20):** User confirmed successful execution. Next: owner-run the fictional notice seed once, then interactive user acceptance/verification. Publication and actual hosted acceptance remain pending. No repeated migration/password setup is needed; no runtime test rerun or agent-hosted write occurred in this documentation checkpoint.

**Temporary fictional notice authorized and locally implemented (2026-10-20):** User agreed to temporary test use with later revisions. Canonical notice, versioned read/acceptance, subject scoping, atomic audit/repeat handling and explicit test checker are implemented; 118 Python/466 contract/151 isolated SQL checks passed. Next: owner applies only 007, then optional fictional notice seed, then interactive user acceptance. No new database password is needed; hosted publication/acceptance and real concurrency/UI remain unverified. Real-use wording/approval/retention inputs remain open; no real-data authorization is inferred. See [privacy runbook](graphiscan/api/PRIVACY_ACCEPTANCE.md).

**Privacy input unavailable (2026-10-20):** User confirmed no approved agreement wording yet. [PRIVACY_REVIEW_BRIEF.md](PRIVACY_REVIEW_BRIEF.md) records product facts and missing institutional/data/retention/approval inputs without inventing policy. Publication/real acceptance stays pending; continue independent generic v1 login/logout and session verification while preserving the closed missing-agreement gate. No runtime or hosted changes in this documentation checkpoint.

**User-run hosted password lifecycle passed (2026-10-20):** Supplied `password-check-passed`, all 12 checks passing: verified fictional sessions/forced gate, actual v1 password endpoint, old credentials/sessions denied, fresh bootstrap, privacy gate preserved and cleanup. The fixture password and first-change state changed; no credentials were received/saved. No repeat setup/checker is needed. Next: obtain approved privacy wording/version, implement agreement acceptance/gates and client onboarding. Standalone hosted success does not establish generic login/logout, refresh/concurrency/recovery, client cutover or resource authorization. Latest automated evidence remains 103 Python, 465 contract and 123 isolated SQL; this update is documentation only.

**Hosted writer verified; password checker ready (2026-10-20):** User saved the separate writer configuration; agent-executed preflight passed 23 read-only hosted checks after explicit session-timeout setup fixed the first lock-timeout failure. New fictional Auth password checker is prepared for manual hidden-prompt execution; no actual Auth password/application record changes have occurred. All 103 Python, 465 contract and 123 isolated SQL checks passed. Next: run the checker with the fictional Auth account's current and newly chosen passwords locally; hosted change/old-credential/session/recovery/concurrency and client integration remain open.

**Writer login reported complete (2026-10-20):** User completed the separate writer LOGIN/password statement privately. Next: run the hidden-prompt connection helper, then verify hosted writer grants/login and Auth password/session/recovery behavior. Six new synthetic helper tests passed separately from the prior 84-test full run. No writer connection or actual password-change verification yet; no repeated SQL setup is needed.

**Hosted migration 006 reported successful (2026-10-20):** User confirmed successful SQL Editor execution. Next is private separate-writer LOGIN/password and DSN setup, then actual hosted writer/password/session/recovery verification. Do not rerun migrations 001-006 or reader setup. This is user-reported execution, not agent-inspected hosted grants; no repeated runtime tests.

**Local password slice implemented (2026-10-20):** First-login/self password endpoint, durable pending/session invalidation, separate function-only writer draft and fictional-account recovery are implemented locally. All 84 Python tests, 465 contract and 119 isolated SQL checks passed. No hosted credential/write configuration changed. Next is reviewed migration 006 plus private writer setup and hosted password/old-credential/session/recovery verification; approved privacy wording and client integration remain open. See [password runbook](graphiscan/api/PASSWORD_CHANGE.md) and refreshed [RESUME.md](RESUME.md). Earlier implementation-next checkpoints below are historical.

**Break/resume checkpoint (2026-10-20):** User requested a break after the passing hosted Auth check. Start with [RESUME.md](RESUME.md) on return. Next work is first-login password-change/session-invalidation implementation and verification; no dashboard action or repeat setup is currently required.

**User-run hosted Auth lifecycle passed (2026-10-20):** Supplied report shows all 11 checks passed: sign-in, verified subject/bootstrap, forced-password gate, local cleanup and revoked-session denial. No application DB writes or saved credentials; no token/password received by agent. This supersedes the earlier failed attempt. Next: implement first-login password change/session invalidation with narrowly scoped writes and failure-path checks, then client onboarding. Approved privacy wording remains needed. No claim of production session endpoints, refresh/concurrency or client cutover; latest automated checks remain 61 Python, 464 contract and 91 SQL.

**Auth sign-in troubleshooting (2026-10-20):** User's first interactive attempt was rejected before session creation. Actual read-only Auth settings check passed (HTTP 200, project key accepted, email provider enabled). Added safe HTTP/category diagnostics and redaction coverage; all 61 Python tests passed. Next: one user-controlled retry with the fictional Auth-account password to identify the rejection category. Successful hosted Auth lifecycle remains unverified; no account/password or SQL changes occurred.

**Interactive Auth checker ready (2026-10-20):** User reported test-profile seed success. Added hidden-prompt fictional-account checker for actual sign-in/verified bootstrap/password gate/local logout/durable session denial without saving or printing secrets. All 58 Python tests passed with provider/DB mocks. Next: user opens a local interactive PowerShell terminal and runs it with the privately saved Auth-account password. No actual Auth lifecycle verification has run yet; v1 login/logout/password-write features remain separate work.

**Fictional Auth/profile checkpoint (2026-10-20):** User reported auto-confirmed Auth test account creation with private credentials. Prepared and isolated-tested optional `seed_test_profile.sql` (synthetic active admin, forced password change, no grants/consent, transactional audit; refuses overwrites). Passed 464 contract and 91 SQL checks. Next: owner runs this seed in the test project, then actual private Auth login/token/bootstrap. No agent-hosted profile mutation/sign-in occurred.

**Hosted read-only checkpoint passed (2026-10-20):** Actual verify-full CA/reader connection and all 24 preflight checks passed; optional token bootstrap not run. Fixed preflight Auth metadata introspection without adding schema grants. All 49 Python tests, 464 contract checks and 84 isolated SQL checks passed. No database writes or client cutover. Next: prepare a fictional identity through Authentication > Users and test actual Auth/token/bootstrap. Provider concurrency/refresh/sign-out, onboarding/resource writes and migration remain open. Continue one user-facing step at a time.

**First connected attempt (2026-10-20):** Private settings and driver/adapter parsing passed; backend opt-in is prepared. Read-only hosted preflight attempted connection and stopped before DB checks due to missing local root certificate. Diagnostic emitted fixed flags only; no DB writes or credential/grant verification occurred. Next: trusted CA download/path configuration, then retry verify-full preflight. Continue one user-facing step at a time.

**Private credential rotation checkpoint (2026-10-20):** User reported a new privately saved reader password and completed ALTER ROLE reset after a password-like value was shared. Next: private DSN password/reader username, project settings/TLS and connected preflight. No credential values are recorded and no agent-hosted verification occurred. Continue one setup step at a time.

**Reader login checkpoint (2026-10-19):** User confirmed privately replacing the ALTER ROLE placeholder with a new password and reported success. Next: private connection/project settings, then connected preflight. No agent password receipt or hosted connection occurred. Continue one user-facing setup step at a time.

**Reader execution checkpoint (2026-10-19):** User reported successful 005 setup. Next: enable its LOGIN with a new password privately, configure local reader/project settings and run connected preflight. No agent connection or credential value was provided; hosted grant/TLS/Auth checks remain pending.

**Restricted reader setup (2026-10-19):** User confirmed expected hosted schema metadata after 001-004. Added isolated-tested but unapplied 005 server reader/session function setup for Supabase's Auth RLS. Reader has no bypass/direct Auth SELECT; snapshot/preflight use a restricted definer function. Passed 49 Python tests, 464 contract checks and 83 SQL checks. Next: run 005, configure reader login/password privately and run connected preflight. Actual agent DB/provider/TLS/concurrency verification remains pending. Existing clients/MySQL remain active.

**User-assisted hosted setup (2026-10-19):** User reported successful SQL Editor execution of all four migrations (001-004) after project setup. This has not been independently verified. Next: run read-only `verify_schema.sql` in the same disposable target, configure the dedicated reader privately and run the hosted preflight. Existing clients and MySQL remain in use.

**Hosted preflight preparation (2026-10-19):** Added a read-only checker and [disposable-target runbook](graphiscan/api/HOSTED_PREFLIGHT.md). Executed offline check: all four v1 settings absent, no network attempt/DB writes. Passed 48 Python tests, 464 contract checks and 73 isolated SQL checks (including 10 catalog checks). No hosted integration claim is made. Next required input is a disposable Supabase target with reviewed 001-004 schema and a dedicated reader configured privately; then run `check_v1_hosted.py --connect`, optionally with a fictional-user access token. Credential/consent/logout writes and full resource/hosted concurrency checks remain open.

**Trusted adapter checkpoint (2026-10-19):** Implemented optional Supabase remote identity verification, one-statement PostgreSQL access snapshots and unapplied 004 session invalidation/floor support. All 38 Python tests, 464 contract checks, 32 prior SQL checks and 31 new isolated SQL access checks passed. Driver installation/configuration was verified locally without connecting to a database. Real Auth responses/signatures, hosted schema/TLS/grants, concurrent provider transactions, credential/consent/logout writes and resource queries remain unverified/unimplemented as applicable. Next: prepare and run disposable hosted integration once a target project is supplied; complete onboarding/session write orchestration and real resource handlers before client cutover. Default v1 setup remains unavailable, and existing clients/MySQL remain active.

**V1 runtime foundation (2026-10-19):** Added registered health/bootstrap handlers and a shared access guard with synthetic runtime tests. Protected v1 access fails closed until durable identity and current-profile adapters are supplied. Existing clients and MySQL routes remain in use. Next: implement/test trusted provider session verification and PostgreSQL access snapshots, then run disposable hosted integration checks. Resource endpoints, credential/consent writes, private storage and migration remain open.

**OpenAPI/schema alignment (2026-10-19):** All 31 proposed operations now have an OpenAPI 3.0.3 draft, accompanied by 19 proposed access cases and unapplied `003_api_contract.sql`. Validation passed 464 specification/declaration/payload checks and 32 PostgreSQL checks in an in-memory database with fictional rows. This establishes draft interface/schema evidence only. Next: implement a minimal v1 health/bootstrap/authorization slice with executable runtime tests, then validate its Auth/Storage/role wiring in a disposable hosted project when access is available. No live migration, service setup or client switch occurred; unresolved privacy/deletion/model/limit inputs still gate their dependent features.

**Shared API contract draft (2026-10-19):** [API_CONTRACT.md](API_CONTRACT.md) defines the proposed `/api/v1` resources, wire types/score units, identity/password/privacy gates, trusted permissions and assignments, parent release, versioned reviews, private images, upload retry/transaction behavior and current-route migration map. Three JSON examples/local links and 31 unique method/path entries passed document checks. The contract is not frozen or implemented. Next technical work is an OpenAPI/access-test specification and reconciliation of the PostgreSQL drafts; approved privacy wording, retention/deletion policy, school/assignment inputs, model evidence and service limits gate their dependent implementation. No migration or hosting changes occurred.

**Resumed (2026-10-19):** User sign-in in the shared Playwright browser succeeded. Populated read-only admin browser checks passed at desktop/phone widths. A pending-result image URL defect was fixed and regression-tested; after removing a stale Flask listener and reauthentication, the actual pending-result image loaded successfully with no displayed errors or document overflow at 1440px/390px. Sampled isolated admin write checks also passed, as recorded below. No migration/deployment has started. See [CHANGELOG.md](CHANGELOG.md).

**Isolated admin write checkpoint (2026-10-19):** Ten API write checks and twenty browser assertions passed using a disposable copy of the current schema with fictional records, first on desktop and then at 390px after the UI fixes. Covered account creation, approve/reject API actions, disable/restore, student creation, guardian change/removal, password-confirmed deletion, linked-record/file cleanup, password change with old-password denial/new-password login, and audit activity. Temporary database/browser/API cleanup succeeded; original database schema/content fingerprints were unchanged.

**Admin UI checkpoint (2026-10-19):** Fixed field/close-button naming, modal and drawer keyboard focus, status/error semantics, small controls, and contrast. The final build passed. Bounded Chromium checks passed at 320px/390px/1440px for the sampled forms, modal focus containment/Escape/return, scroll locking, and simulated slow/failed/offline/empty responses and save retry. The core admin baseline is usable for shared API contract work. Complete screen-reader/physical-device coverage, text zoom, remaining error cases, and older Flask session parity stay on the release checklist; this is not a full accessibility certification or a migrated/hosted release.

**Earlier admin checkpoint (2026-10-17):** Live read-only API baseline passed all 26 status checks, including populated admin list/detail requests and role denials. Admin API sessions now follow current database account role/status; 7 synthetic regression test methods passed. Real-browser signed-out checks passed for 7 route redirects, login layout at 390px/1440px, password visibility, and invalid login. Authenticated browser and sampled write checks subsequently passed on 2026-10-19 as recorded above; older Flask session-state checks remain open.

**Preparation checkpoint (2026-10-17):** Preparation and admin baseline checks started. Both Vue builds and two synthetic parent-access tests passed; Settings route login metadata corrected and admin rebuilt successfully. Fresh local database backup/restore now passed for all 8 tables, with matching schemas and content hashes; private source/assets archive integrity passed. Populated authenticated browser workflows and application boot from restored assets remain open. Preparation still needs the remaining inputs and recovery coverage.

This is an ordered set of goals and completion checks, with no calendar deadline attached. Move to the next dependent piece when its check passes. Keep a working current-stack demonstration while replacements are being built. Source changes alone do not prove that a feature works with real accounts, a database, or a device.

| Sequence | Goal and work | Completion check | Panel items |
| --- | --- | --- | --- |
| **1. Protect the current system and gather inputs** | Agree on the demonstration scope and owners. Collect the manuscript, slides, approved privacy-agreement text, hosting and device access, and a fresh MySQL schema/data export. Make a backup and restore-test it. | The existing system can be recovered, and the inputs needed for the next phases are available. | Prerequisite for all |
| **2. Finish the existing admin web app** | Review result, student, progress, account, settings, and audit screens with real role-based data. Fix misleading screening language and broken actions. Keep Vue for admin. | Production build and main authenticated workflows pass at desktop and phone widths, including populated detail pages. | 2, 3, 5 |
| **3. Define the shared API and prepare test hosting** | Settle the account, school, student, result, validation, report, model/version, and image-access contract. Prepare separate test environments for Supabase PostgreSQL/Auth/private Storage, Flask and its model, Vue admin hosting, and Expo Android builds. Configure server-only secrets, public API origins, permissions, and billing alerts. | A test admin build, API health request, database connection, and Android build reach the intended test services; no secret is in a client bundle. | Foundation for system items |
| **4. Prepare hosted data with a rollback path** | Apply and review the PostgreSQL schema; map users, schools, Grades 1–3, historical binary results, expert reviews, and report history. Migrate a copy of records and images into private storage while retaining the current MySQL system. | Row counts and relationships reconcile, authorized image access works, and a rollback rehearsal succeeds. | 9, 11 |
| **5. Enforce accounts and record access** | Connect durable authentication to Flask. Add admin-issued temporary accounts, required first-login password change, approved agreement acceptance, school/student ownership, role checks, and expert-to-parent release rules. Cover JSON APIs and older Flask routes until they are retired. | API tests show each role sees only authorized records and cannot bypass onboarding or reach unreviewed parent results. | 3, 9, 10 |
| **6. Finish screening behavior and model evidence** | Make Initial/Follow-up assignment transactional. Record model key/version, task type, class scores, report type, and expert status while preserving binary history. Compare ResNet, EfficientNet, and MobileNet on one documented three-class split; review per-class errors and the missing writer IDs. Add a default and selector only if the evidence supports them. Keep AI advice absent. | Concurrent uploads cannot create two Initial reports; history and expert review work; model reports and labels match the deployed model. | 1–5, 11 |
| **7. Replace mobile flows in slices** | Build the Expo shell and login gates once the API contract is stable. Complete teacher capture/results, expert review, parent history, and guest demo as separate checkpoints. Use Vue/Capacitor as a behavior reference until the native app reaches parity. | A physical Android release build completes every core role flow against the shared API. | 3, 5, 8–11 |
| **8. Align the manuscript and presentation** | Update objectives/model names, Background, themed literature review, scope, account/privacy and screening workflow, methodology image, WBS, shared use cases, Use Case Diagram, DFD/CFD, slide wording, and nonfunctional requirements as system evidence becomes available. | The paper and slides match observed behavior; each of the 16 panel comments has evidence or a stated limitation. | All 1–16 |
| **9. Integrate and release** | Rehearse migration and rollback; run populated admin/mobile and role-access checks, accessibility and responsive review, physical-device flows, model-history checks, and hosted response-time measurements. Align or retire old Flask pages. Fix findings before cutover. | The release gates below pass, the demonstration is accurate, and the old database/mobile release are retired only after verified replacements work. | Close 1–16 |

The manuscript and slides can advance alongside the code when their source files and an owner are available. Model comparison can also proceed while the shared API is built, but deployment of a new model waits for its evaluation and storage contract. Start the Expo shell after the API contract is stable; complete each role as its server behavior becomes ready. Record what changed, what was tested, and what remains at each checkpoint.

**Technology direction:** Keep Vue for the admin website and Flask for the API/inference service. Replace Vue/Capacitor for mobile with React Native/Expo. Move from XAMPP/MySQL to hosted Supabase PostgreSQL/Auth/private Storage after migration and access checks pass.

**Scope decision:** If the export, privacy text, manuscript/deck, hosting access, or implementation capacity is unavailable, keep a truthful current-stack demonstration and identify unfinished hosted-data, native-mobile, or three-class-model work. Do not treat a planned feature as complete because it appears in this sequence.

**Release gates:** A backup restores and migrated records reconcile; protected APIs enforce role and ownership; first-login and agreement gates work; parents cannot access unreviewed labels; concurrent screenings produce only one Initial report per student; model/version and historical binary results remain accurate; private images are accessible only to authorized users; and the Expo release build completes core flows on a physical Android device.

## Defense action tracker

**Working agreement (2026-10-17):** Follow both the panel comments and the team’s stated “Action/s Taken” in `GraphiScan_Defense_Minutes.md` as the implementation commitments. Although that column uses past tense, treat each action as work to implement or verify until evidence establishes completion. Do not silently substitute different behavior or expand the agreed scope. Where wording conflicts or needs a substantive decision, resolve it with the user before implementing the dependent change. Existing architecture decisions remain separately recorded project decisions.

Source: [GraphiScan_Defense_Minutes.md](GraphiScan_Defense_Minutes.md) (June 1, 2026), supplied and reviewed on 2026-10-17. All 16 transcribed recommendations are represented below. Tracker numbers are internal references and do not follow the source document’s section order. The minutes’ “Action/s Taken” column records reported actions; it does not establish that the present code or manuscript implements them. The context file describes the original manuscript and may conflict with the panel.

The minutes specify elementary students grouped by school and grade; Grades 1–3 is the separately recorded project scope. Expo, Supabase, and hosting choices are project architecture decisions, not requirements stated by these minutes.

The rows below preserve the historical source-inspection baseline. Several
implementation statuses have since advanced; use the complete current16-item
matrix in [CURRENT_REQUIREMENTS.md](CURRENT_REQUIREMENTS.md). Actual hosted
schema/admin evidence is recorded in the newest CHANGELOG and KNOWLEDGE entries.

| # | Applies to | Manuscript / presentation action | System action and current status |
| --- | --- | --- | --- |
| 1 | System + manuscript | Report the evaluation method and scores for all compared models consistently. | **Open:** Target PostgreSQL model registry and result-to-model relationship are drafted but not applied. Integrate ResNet, EfficientNet, and MobileNet; default to the best on the same held-out three-class evaluation and allow selection. Live code loads only one binary ResNet50 model. |
| 2 | System + manuscript | Remove unsupported AI advice from the manuscript or document an evidence basis. The minutes say it was removed. | **Changed in source, runtime unverified:** The predictor no longer emits canned advice or analysis prose; new result rows write empty values to the legacy required recommendation/summary columns. Current Vue result views and main Flask result/report pages do not show older stored AI prose. Older values remain in the database until migration cleanup. Expert-written notes remain attributed to the expert. Manuscript text still needs review. |
| 3 | System + manuscript | Revise objectives to include expert validation and clarify that any human recommendation follows analysis. Reconcile this with item 2: removing **AI** advice does not remove expert-authored recommendations. | **Partial:** Expert review/flag routes and screens exist. Current parent result routes and older Flask pages release only linked `Validated` results; synthetic-record API tests passed. Check the full report flow with a live database and preserve this rule during migration. |
| 4 | Manuscript | Name the trained models in the objectives and explain why each was trained. | Item 1 covers the related model-selector implementation. |
| 5 | System + presentation | Improve text colors and font styles for readability, smooth slide transitions, and clearly highlight High Potential / Low Potential classifications when supported by the deployed model. | **Partial, source only:** Admin and current Vue mobile result/progress copy was simplified; unsupported score trends and clinical probability labels were removed from those views and progress API responses. Visual layout and presentation still need review. Live inference is binary; do not display Low before a validated three-class model exists. |
| 6 | Manuscript | Strengthen Background of the Study: problem, gap, significance. | No code change implied. |
| 7 | Manuscript | Reorganize literature review into three or four themes with italicized headings. | No code change implied. |
| 8 | Manuscript diagram | Show shared use cases involving two or more actors. | Existing teacher → expert → parent workflow should match the diagram; the comment does not itself request a new feature. |
| 9 | System + manuscript | State elementary participants and grouping by school and grade in Scope and Limitations. The context specifies Grades 1–3. | **Open:** Target PostgreSQL schools and grade constraints are drafted but not applied. Current student records have grade but no school. Add school data and grouping in API/admin/mobile. |
| 10 | System + manuscript | State that the GraphiScan team (administrator or authorized researchers) creates and provides a temporary account for each user. The user changes that temporary password on first login, then reads and accepts the Data Privacy Agreement before accessing features. | **Partial:** Public registration is now refused in source. Target PostgreSQL identity/consent tables are drafted in `graphiscan/db/postgres/001_identity.sql` but not applied. Issuing temporary credentials, forced first-login change, and agreement gates are absent. Approved agreement wording is needed. |
| 11 | System + manuscript | Explain Initial versus Follow-up screening in workflow and reports. | **Partial:** Both upload paths label first/later reports; recorded labels now reach React result/history screens via all nine role reads. Isolated read/scope tests and React builds pass; live/device checks remain. Target PostgreSQL schema limits one Initial per student; serialize concurrent screening assignment during API migration. |
| 12 | Manuscript | Replace the methodology image with the Integrated Hybrid Project Management Approach model. | No code change implied. |
| 13 | Manuscript | Remove unnecessary WBS components and align it with that methodology model. | No code change implied. |
| 14 | Manuscript diagram | Revise and reorganize the Use Case Diagram. | Compare its actors and actions with the final application. |
| 15 | Manuscript diagrams | Align the DFD with the CFD. | Compare both with the final data flows after API/storage migration. |
| 16 | Manuscript + system evidence | State the non-functional requirements in the paper. | Measure the stated response-time and other requirements on the final deployed system; they cannot be marked achieved from source alone. |

The manuscript source and presentation deck are not in this workspace. The minutes' reported “Action Taken” text has not been treated as proof that the corresponding manuscript files or system features are complete.

### Consistency rules

- GraphiScan is a screening aid, not a diagnosis. Any probability must state which model and class it represents. A confidence score is not a clinical probability.
- Use exactly `Normal`, `Low Potential`, and `High Potential` only after a validated three-class deployment. Until then, the live system is explicitly binary (`Normal` / `High Potential`).
- Do not infer `Low Potential` by renaming a binary `Normal` result or compare the binary 86.03% result directly with a three-class score.
- AI-generated recommendations are no longer produced or displayed in current source. Remove the obsolete database column and any older stored values during migration; expert-authored observations may remain, clearly attributed to the expert.
- The same account, student, screening, result, and expert-validation rules must apply to the admin website, mobile app, and API. The API is the authority.
- The older Flask-rendered routes remain reachable in source, so changes to shared behavior must cover or retire those routes before deployment.
# Superseded migration checkpoint2026-10-22

The earlier020 privilege gap was resolved by user-applied021. The last required
hosted preflight passed38 checks and matching assignment API/admin source was
published in merged PR#5. Do not rerun020/021. Actual authenticated assignment
behavior and historical-data/image cutover remain separate open checks.
