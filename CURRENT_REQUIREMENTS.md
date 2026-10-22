Current handoff2026-10-22: migrations020/021 are applied and the last hosted
read-only preflight passed38 checks. PR#5 assignment API/admin and PR#6 shared
page/card styling are merged. Public bundle index-BMML1qyx.js contains the shared
cards, headers and centered Logout; public login returned200. Authenticated
assignment/permission/audit and reset/delete checks remain open. Expo integration
can begin against the deployed API; hosted inference is disabled, real-use privacy
publication is pending, and historical MySQL data/image transfer is incomplete.
No additional numbered migration is currently prepared. Do not rerun020/021.
# GraphiScan current requirements and next steps

Reviewed 2026-10-22 against all35 project Markdown files present before this
audit, the latest session evidence and the OpenAPI operation declarations.
Dependencies, generated output, local tools and skill documentation are excluded.
This is a documentation review; no new tests, account writes or migration ran.

## How to read the evidence

The defense minutes contain16 commitments. Their past-tense Action/s Taken
column is a requirement to substantiate, not completion evidence. Grades1-3,
Supabase, Expo and the hosting choices are separately agreed project decisions.
Use the newest dated evidence when old checkpoints conflict. A source handler,
synthetic check, schema installation and real hosted workflow are different facts.

## Current foundation

Assignment access update2026-10-22: source now implements explicit eligibility
administration through a scoped API and Edit dialog.607 contract/
507 isolated SQL/77 focused Python checks and responsive preview/build passed.
020/021 are applied; the required hosted preflight passed38 checks and PR#5
published matching source. PR#6 shared admin layout is also published. Verify hosted
behavior. [Assignment rollout](graphiscan/api/ASSIGNMENT_ACCESS.md) records scope.

Latest verification2026-10-22: PR#3 merged and the public bundle includes the Edit
actions.574 contract/466 isolated SQL checks and46 focused Python tests pass,
including current route parity, global-only grant scopes and issuance/reset/delete
saga boundaries. This is separate from hosted provider/credential verification.
This earlier check preceded the prepared020 assignment-management slice above;
school membership alone still does not grant assignment eligibility.

Subsequent authorized hosted checks (2026-10-22): one fictional account was
created201, edited200, disabled/reactivated200 and had its temporary synthetic
school membership removed200. Reset/delete still require private issuer-password
entry; no completion claimed yet. Seventeen isolated admin tests pass after
updating stale optional-migration mocks. Other release gaps below remain open.

| Area | Current evidence | Still open |
| --- | --- | --- |
| Admin | Vue/Vite refinement and Edit actions published; fictional hosted create/edit/disable/reactivate/membership changes observed | Hosted reset/unused-delete, permissions, school/student assignments, errors and audit walkthrough |
| API | Lightweight Flask/Gunicorn API Live on Render Free/Singapore; now tracks merged main | Full authenticated role/Storage/write verification; hosted inference explicitly disabled |
| Supabase | Schema through021 applied; last required preflight passed38 checks | Historical MySQL record/image import, identity mapping, reconciliation and rollback |
| Accounts | Issuance, guarded edits, reset/delete/onboarding source; assignment-access API/admin published in PR#5 | Hosted eligibility use, new issued-user onboarding, approved real-use agreement and scoped permission verification |
| Models | Three binary architectures locally reevaluated on136 test images; catalogue publication checker previously passed12 checks | Free inference host, hosted execution, three-class dataset/evaluation and final deployment |
| Expo | Hosted HTTPS default, branded onboarding, role-aware Home/tabs and refined read screens; TypeScript and Android bundle export passed; fictional layout review | Real hosted/device checks, hosted student-creation parity, model-enabled upload; no APK generated/released |
| Documentation | Requirements, contracts, runbooks and proposed privacy text available | Editable manuscript/deck, approved wording, diagram revisions and final measured nonfunctional evidence |

Admin: https://graphiscan-admin.vercel.app/login

API: https://graphiscan-admin-api.onrender.com

GitHub PR#1 merged as `2ddb85f`; Render's main-branch deployment succeeded/live.
Hosting/checkpoint and `render.yaml` alignment are saved in merged PR#2; PR#3
contains the published Edit actions. Do not upload generated output or private bundles.

## All16 panel commitments

| # | Requirement | Current assessment / remaining work |
| --- | --- | --- |
| 1 | Integrate ResNet, EfficientNet, MobileNet; best evaluated default and manual selection | Binary catalogue/runtime/selector source and publication evidence exist. At the current0.75 rule MobileNetV2 ranked highest on the available split. Hosted inference and planned common three-class comparison remain open. |
| 2 | Remove unsupported AI recommendations | Current predictor/API/display source removes canned AI advice. Historical database cleanup and manuscript review remain; preserve attributed expert remarks. |
| 3 | Objectives focus on analysis, justified recommendations and expert validation | Review/assignment/release source exists. Complete teacher-to-expert-to-parent hosted flow and align objectives. Parent access requires linked, Validated reports. |
| 4 | Name models and their purpose in objectives | Needs editable manuscript review. |
| 5 | Readability, classification emphasis and presentation transitions | Admin styles refined and published; mobile/device accessibility and actual slide transitions remain. Never fabricate Low Potential from a binary model. |
| 6 | Background pages2-5: problem, gap, significance | Manuscript source/revision evidence needed. |
| 7 | Literature pages10-12: three or four themes, italicized headings | Manuscript source/revision evidence needed. |
| 8 | Shared use cases for two or more actors | Diagram needs teacher/expert/parent shared interactions matching actual access rules. |
| 9 | Elementary participants grouped by school/grade | Hosted schema, API and directory UI exist, with agreed Grades1-3 constraints. Verify populated assignments/filtering across roles/mobile; reconcile imported schools/grades. |
| 10 | Admin/authorized researcher issues accounts; first-password change then privacy acceptance | Technical source and earlier fictional gate evidence exist, plus one issuance. Public-host onboarding/role checks and approved real-use agreement remain. No public registration. |
| 11 | One Initial Screening; all later completed screenings Follow-up | Transactional hosted source/constraints and recorded-history views exist. Real upload/retry/concurrency and released-history checks remain. |
| 12 | Integrated Hybrid Project Management Approach image on page24 | Needs manuscript source and matching final figure. |
| 13 | WBS page26 aligned to methodology, unnecessary work removed | Needs manuscript/WBS source review. |
| 14 | Reorganize Use Case Diagram page38 | Needs diagram source and final actor/action reconciliation. |
| 15 | Align DFD pages39/41 with CFD | Needs diagram source reflecting API, Auth, database, private images, inference and expert release. |
| 16 | State nonfunctional requirements pages34-36 | Requires actual manuscript targets and deployed/device evidence for response time, access, recovery, usability and reliability. Sleeping free API is not proof of the five-second result target. |

## Important limitations to preserve

- Existing comparison evidence is binary: Normal / High Potential. The agreed
  three-class target remains Normal / Low Potential / High Potential; it needs
  suitable labels, evaluation and integration. Do not relabel old binary results.
- Historical training CSV accuracy and current preprocessing/threshold accuracy
  differ. Use `api/MODEL_EVIDENCE.md` for the matching metrics and split limits.
  Writer separation is unverified; a screenshot is not accuracy validation.
- Current hosted notice is for a bounded fictional audience. The formal preview
  is an unpublished draft. Do not clear the audience or invent acceptances to
  onboard a new user; approved publication/audience setup is a separate dependency.
- School memberships/permissions do not automatically create every trusted
  assignment eligibility. Directory writes require existing authorized candidate
  eligibility. The management API/UI is published with020/021 installed;
  its local tests do not establish hosted new-account linking.
- Private Storage primitives previously passed a generated-object check; this
  does not establish real hosted screening/image/report authorization end to end.
- The production composition excludes legacy MySQL routes. Legacy Vue/Capacitor
  and Flask source remain separate; archive/retire only after required parity and
  migration recovery are established.
- Guest demo is excluded from the current core work. Do not add it back because
  older diagrams/contracts mention it. `/summary` is proposed; current dashboard
  counts correctly describe loaded records, not verified global totals.
- OpenAPI declares36 foundation operations and2 proposed operations; those tags
  describe source coverage, not36 verified production workflows. Two foundation
  operations use the installed020 migration.

## Recommended execution order

User reconfirmed presentation targets2026-10-22: admin is desktop browser first,
with responsive fallback; Expo is native Android. Use web previews only as an
engineering aid, with APK/device evidence required for mobile completion.

1. **Close hosted admin behavior gaps.**020/021 are applied and passed the
   read-only preflight; matching source is published. Do not rerun migrations.
   Walk through a controlled fictional
   account's admin lifecycle and school/student/permission/eligibility actions,
   including audit and denied operations. Fix demonstrated gaps. Do not rerun019.
2. **Continue Expo on Android.** Hosted HTTPS is now the source default, with
   password/privacy gates and role-aware read screens. Complete real issued-user
   sign-in, gates, scoped lists/history and remaining student-creation parity on
   device. Browser layout fixtures and bundle export do not prove native behavior.
   Keep server secrets out of public Expo variables.
3. **Enable a free model-capable backend.** Check artifact memory/startup and
   available provider constraints before selecting a host. Current Render admin
   service has no inference framework/artifacts. A separate remote model call is
   not implemented; either deploy the model-enabled API or explicitly implement
   and verify a bounded server-side integration. Do not promise a provider yet.
4. **Complete the real core workflow.** Teacher sample/model choice -> Initial
   result -> admin expert assignment -> expert Validated/Flagged review -> linked
   parent's released report/private image -> Follow-up history. Include retries,
   revocation, failure cleanup, wrong-role denial and concurrent Initial protection.
5. **Finish model requirements and required historical cutover.** Validate the
   three-class dataset/split and models; preserve binary history. Resume legacy
   export/import only with an authoritative recoverable source, reviewed identity
   mapping, reconciliation and rollback. MySQL repair is currently paused.
6. **Complete Android and paper release evidence.** Build an APK, check core
   roles on a physical device, measure nonfunctional targets and update report
   screenshots/model tables. Manuscript, diagrams, slides and approved privacy
   wording can progress alongside independent engineering work when supplied.

The immediate implementation priority is item1; Expo follows it. Steps describe
planned work, not newly authorized test/account mutations or completed behavior.

## Markdown coverage

- Requirements/governance: `AGENTS.md`, `GraphiScan_Defense_Minutes.md`,
  `SYSTEM_DESIGN.md`, `PROJECT_PLAN.md`, `WORK_CHECKLIST.md`, `API_CONTRACT.md`.
- Evidence/overview: `KNOWLEDGE.md`, `CHANGELOG.md`, `RESUME.md`, `README.md`.
- Presentation/privacy: `PRESENTATION_READINESS.md`, `PRESENTATION_REHEARSAL.md`,
  `PRIVACY_REVIEW_BRIEF.md`.
- Database: `db/MIGRATION_NOTES.md`, `db/BACKUP_RESTORE.md` under `graphiscan/`.
- API under `graphiscan/api/`: `README.md`, `ADMIN_RELEASE.md`, `ADMIN_WRITES.md`,
  `DIRECTORY_ACCESS.md`, `DIRECTORY_WRITES.md`, `WORKSPACE_DIRECTORY.md`,
  `SESSION_INTEGRATION.md`, `PASSWORD_CHANGE.md`, `PRIVACY_ACCEPTANCE.md`,
  `PRIVACY_AGREEMENT_DRAFT.md`, `SCREENING_READS.md`, `SCREENING_WRITES.md`,
  `MODEL_EVIDENCE.md`, `HOSTING.md`, `HOSTED_PREFLIGHT.md`, `FICTIONAL_WORKFLOW_SETUP.md`.
- Clients/assets: `graphiscan/admin-web/README.md`,
  `graphiscan/admin-web/src/assets/README.md`, `graphiscan/user-app/README.md`,
  `graphiscan/mobile-app/README.md`.

Many older dated runbooks still describe the state when their slice was added.
Do not follow their old pending-migration/setup instructions over an installed
project. This audit and the newest changelog take precedence for current status.
