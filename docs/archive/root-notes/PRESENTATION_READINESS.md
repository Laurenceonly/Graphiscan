# Presentation readiness - 2026-10-20

User target: present this afternoon, approximately **2-3 PM Asia/Manila**.
Time checked: approximately **7:43 AM**, leaving about 6-7 hours.

Latest user steering: stop guest-demo work and focus on the agreed core scope.
Guest removal is planned, not implemented. The earlier proposal to concentrate
on presentation rehearsal does not override this direction. Core shared
login/logout and client onboarding integration are next implementation priorities;
the existing clients still use MySQL authentication. No optional guest test is
needed for the next step.

## Progress estimate and evidence

**Full planned rebuild: roughly 25-35% (latest estimate about 32%).** This is
engineering judgment across the remaining API/data migration, authorization,
model evidence, native app, hosting and documentation work. It is not a measured
task-completion statistic or a claim that the system is production-ready.

The current prototype is a separate, more mature demonstration candidate:

| Area | Current evidence |
| --- | --- |
| Backup | Current MySQL schema/content restore check passed; full app recovery rehearsal remains |
| Existing admin | Main populated routes and sampled writes passed earlier desktop/phone checks; fresh presentation rehearsal remains |
| Hosted foundation | Reader/writer preflights passed 24/23 checks; migrations 001-007 user-reported applied |
| Auth/password | User-run Auth/password lifecycle passed 11/12 checks; old password/sessions denied and fresh sign-in worked |
| Temporary privacy notice | User-run hosted explicit acceptance passed all nine checks, including stale-version denial/readiness/cleanup; fictional testing only |
| Fresh frontend builds | Admin and user Vue production builds passed on 2026-10-20 |
| Fresh local API | All 26 read-only existing-MySQL checks passed with zero failures; real browser login/writes/inference still require rehearsal |
| Running rehearsal services | Local Flask on 5000 (debug/reloader off), admin on 5173, user app on 5174; API health and both frontend roots returned 200 |
| Current admin navigation | User-confirmed Dashboard, Users, Students, Results, Progress, Audit Logs and Settings loaded; detailed/write and other-role rehearsal still separate |
| Teacher screens | User-confirmed dashboard, student list, results list and one existing result work; fresh upload/inference/write flow remains separate |
| Expert screens | User-confirmed dashboard, results and existing review image/details work; validation submission remains separate |
| Parent screens | User-reported working; populated released-result availability was not separately confirmed |
| Guest inference preparation | Fixed two broken dashboard links to `/guest/demo`; rebuild passed; fresh guest screening remains pending |
| Local regressions | Latest 118 Python, 466 contract and 151 isolated SQL checks passed |
| Latest session/client slice | `/access` onboarding in both apps and login/refresh/logout implemented; 129 Python/seven JS-client/494 contract/165 SQL checks plus both builds passed; hosted 008/browser check pending |
| Main remaining rebuild | Resource endpoints/record scope, private storage/data migration, three-model evidence/integration, Expo app, hosting/release, manuscript/slides |

A fresh working-demo percentage cannot be justified until the selected flows are
rehearsed. Subsequent local socket checks found the three demo ports free, and
the services were started for rehearsal. The Vue clients still use the existing
MySQL API; use existing app accounts, not the fictional Supabase account.

## Proposed afternoon scope - awaiting user's presentation expectations

Demonstrate the existing Vue/MySQL prototype and show verified hosted
authentication/password progress separately. Clearly identify the binary model,
temporary fictional notice and unfinished migration/native app. The complete
hosted/Expo/three-model release should not be promised for this afternoon.

Suggested priorities after the user confirms the expected presentation:

1. Explicit privacy test is now passed; preserve the report as progress evidence rather than rerunning it.
2. Start/check the existing demonstration services and rehearse the chosen
   admin, teacher, expert and parent flows using authorized demonstration data.
3. Fix failures on that route through the demo; preserve the working stack.
4. Prepare a concise progress/evidence slide and list limitations accurately.
5. Rehearse, keep a recovery copy and freeze changes before presentation time.

The proposed scope is not yet an agreed reduction of project requirements.
Do not repeat migrations, seeds or password setup for the presentation.

Use [PRESENTATION_REHEARSAL.md](PRESENTATION_REHEARSAL.md) for the screen checks
and a concise speaking order. No currently signed-in browser was available to
the automation connector; do not describe manual-pending screens as freshly
browser-verified by the agent.
