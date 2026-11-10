# Defense software acceptance audit

## Current reassessment - 2026-11-09

This section supersedes conflicting November 3 status below. Reviewed the defense
minutes, current predictor, hosted upload selector, onboarding guards, screening
read/write SQL, model evidence and newest release/verification records. This was
a source and recorded-evidence audit; no new live workflow or device tests ran.
Paper, diagrams and slide edits are excluded from this reassessment.

**Verdict: the main system features requested in the minutes are implemented;
complete installed-app/hosted acceptance is still unverified.**

| Minutes requirement | Current system status | Remaining evidence |
| --- | --- | --- |
| Three models, highest evaluated accuracy default, manual selection | Implemented. Hosted selector reads selectable registry models and selects is_default. Recorded catalogue check covered all three; MobileNetV2 leads the matching 0.75 runtime evaluation at 85.2941% on 136 images. | Actual installed-app hosted submissions with all three choices and returned identities. Historical training CSV uses a different pipeline/ranking. |
| Remove unsupported AI recommendations | Current predictor returns no advice; reports attribute recommendations to expert review. | Full role/report walkthrough; historical-data reconciliation only if older records are retained/imported. |
| Expert validation and justified recommendations | Assigned-expert review, remarks/recommendation and follow-up fields implemented. Parent SQL release requires a linked student and Validated review. | Complete hosted teacher -> assignment -> expert -> parent flow, including denied/revoked access. |
| Readable text and highlighted classifications | Implemented and supported by recorded browser and selected native checks. | Physical-device/font-scale/long-text acceptance. Current runtime outputs Normal or High Potential only. |
| Elementary students organized by school/grade | Implemented for the separately agreed Grades 1-3 scope; directories, filters and student details exist. | Complete populated cross-role scope/filter/pagination acceptance on installed APK. |
| Admin-issued accounts; first-password change; privacy agreement gate | Implemented with server gates and mobile setup screens; earlier hosted password/privacy checks recorded. Final account delivery is manually entered login email and direct temporary-password handover. | Fresh deployed issued-user onboarding on installed APK. Latest reviewed requirements still leave approved real-participant privacy wording/audience unresolved. Email delivery is no longer required by the agreed direction. |
| Initial then Follow-up screenings | Implemented in transactional completion and stored report types, with student locking and recorded isolated SQL coverage. | Actual successive hosted uploads/history, uncertain retries and concurrency acceptance. |
| Shared actor interactions | Implemented across teacher, admin, expert and parent. | One complete hosted installed-app walkthrough; diagram revision excluded. |
| Nonfunctional behavior | Automated contract/SQL/client and fictional browser checks recorded. | Measured deployed response time/recovery and physical-device usability against stated targets. |

Android 1.0.2 is published: newest CHANGELOG records matching signer/digest,
emulator update-install/launch and live download verification. Earlier statements
that no APK exists or the domain is unconfigured are historical. Latest release
evidence includes 24 mobile tests, 29 shared tests, 8 screening API tests, 654
contract checks/all isolated SQL suites and fictional cross-role browser checks;
these do not establish one complete live role workflow.

Two scope distinctions:

- Low Potential appears as an example in the minutes, not an explicit demand for
  three classes. User explicitly removed the earlier three-class plan on November
  9. Retain Normal / High Potential across all three models; three-class work is
  not a completion gap. Earlier references below are historical and superseded.
- A final screening-cycle summary/conclusion is required by the user in this
  session. Implemented locally after this audit;030 is installed and independently
  metadata/source-verified. API/mobile publication remains. User clarified follow-ups are optional; a reviewed
  Initial with latest Follow-up needed=No can conclude. Existing per-screening
  reports remain distinct. Not explicitly required by the transcribed minutes.

Next acceptance priority: a controlled installed-APK Initial -> expert review ->
parent release -> Follow-up walkthrough, all three model submissions, onboarding
and denial/retry checks, followed by device/performance evidence. No account,
student, review, consent, schema or deployment changes were made by this audit.

Latest initial-review result (2026-11-03): [docs/archive/root-notes/UI_FLOW_CHECK.md](docs/archive/root-notes/UI_FLOW_CHECK.md)
records77 fictional browser flow checks,216 public-page checks,74 admin checks,
successful Results/history read recovery,17 typography checks and36 public
admin-link-removal checks. Landing build and Android/web asset export passed.
Native runtime capture was blocked by emulator ADB timeouts. Signed APK,
physical-device and complete hosted role/Storage/inference acceptance remain open.

Reviewed 2026-11-03. User states defense is 2026-11-11 (eight days away).
Latest steering: user reports graphiscan.site purchased. Connection to Vercel/DNS
is not verified. Target public landing is responsive across phones/tablets/desktop;
admin is laptop-first with mobile support; users primarily use the Android APK.
Initial fictional browser flow reached Initial, review/release and Follow-up;
the full viewport/error/revocation matrix still needs its final rerun.89 combined
Python workflow regressions passed after correcting NumPy test isolation. Added a
mobile Results/history Try again action after demonstrating missing read recovery;
post-change browser/native checks remain open. No actual hosted role flow is claimed.
Later same-day update: account email/direct-handover source is implemented locally;
see graphiscan/api/ACCOUNT_DELIVERY.md.41 focused Python tests passed with approved
access to the installed interpreter. The earlier missing-interpreter report below
was a sandbox access symptom, not proof of a broken installation. Sender setup,
actual inbox delivery, deployment and full Android acceptance remain open.
Manuscript, diagrams and presentation edits are deferred. This file checks the
software implications of all 16 transcribed defense commitments against current
source and recorded evidence. It does not certify a completed APK.

**Verdict: software requirements are partly implemented and locally verified;
the standalone Android release and complete hosted role workflow are not yet
verified. Do not describe the APK or all defense requirements as complete.**

## Panel requirement coverage

Numbers match CURRENT_REQUIREMENTS.md; wording is grounded in
GraphiScan_Defense_Minutes.md, including its Action/s Taken commitments.

| # | Software acceptance condition | Current evidence | Remaining acceptance work |
| --- | --- | --- | --- |
| 1 | ResNet, EfficientNet and MobileNet available; highest evaluated accuracy is default; manual choice works | Versioned binary runtime/catalogue and mobile selector implemented. Recorded common runtime evaluation ranks MobileNetV2 highest at the deployed 0.75 rule (85.2941% on 136 images). Prior supplied browser evidence shows one MobileNetV2 Initial result. | Exercise all three model choices on Android against hosted inference; verify returned model/version and default. Three-class evaluation remains separate unfinished work. |
| 2 | Remove unsupported AI recommendations | Predictor output excludes canned advice; hosted mobile/admin show attributed expert remarks/recommendations. | Inspect actual result/report screens for every role; reconcile obsolete stored AI prose during historical-data migration. |
| 3 | Expert validation and justified human recommendations | Expert review form, revision/idempotency handling and assigned-expert checks exist. Parent reads require linked student and Validated status in SQL. | Complete real assignment/review/release and denied access, including Flagged/revoked access to detail/report/image. |
| 4 | Name models and purpose in objectives | Paper-only wording; model source is covered by #1. | Deferred manuscript task; no new software feature implied. |
| 5 | Readability and visible classifications | Shared native colors/type/status components and model-score explanation exist; previous fictional browser/native-login checks recorded. | Verify role screens, long text/font scaling, dark mode and classification emphasis on installed Android. Current binary runtime cannot produce Low Potential; planned three-class target is unfinished. Slide transitions are deferred. |
| 6 | Background discussion | Paper only. | Deferred. |
| 7 | Themed literature review | Paper only. | Deferred. |
| 8 | Shared interactions involving multiple actors | Software supports teacher upload, admin expert assignment, expert review and parent release in source. | End-to-end execution is still required; diagram work deferred. |
| 9 | Elementary students organized by school/grade | Hosted schema restricts grades to 1-3; mobile school/grade filters and scoped student editor exist. | Verify populated directories, ownership, assignments, filters and paging across actual roles on Android. Grades 1-3 is the agreed project scope, more specific than the panel's elementary wording. |
| 10 | Admin/researcher issues accounts; first-password change then agreement before features | Issuance/onboarding server source and mobile gate screens exist; previous standalone hosted password/privacy checks and fictional issuance recorded. | Verify newly issued accounts through deployed mobile onboarding and protected-route denial. Current bounded fictional notice is not approved real-use policy. |
| 11 | First screening Initial, later screenings Follow-up | Completion SQL locks student row; unique partial index limits one Initial per student. Mobile uses saved report type, not list order. Fresh isolated SQL checks passed. | Run actual second upload/history; test uncertain retry and concurrent requests against hosted service; verify expert/parent report history on Android. |
| 12 | Methodology image | Paper only. | Deferred. |
| 13 | WBS alignment | Paper only. | Deferred. |
| 14 | Reorganized Use Case Diagram | Diagram only; software flows checked under #3/#8. | Deferred diagram task. |
| 15 | DFD/CFD alignment | Diagram only; architecture references exist. | Deferred diagram task. |
| 16 | Nonfunctional requirements | Local access/retry/SQL/client checks exist. | Measure actual deployed response time, access, recovery and native usability against agreed targets. No full performance/device acceptance established. |

Low Potential is mentioned by the panel as an example of classification emphasis;
the three-class target is also an existing project decision. It must not be
fabricated by relabeling a binary result. Historical training accuracy and current
runtime accuracy differ; use graphiscan/api/MODEL_EVIDENCE.md for matching metrics.

## Account delivery direction agreed on 2026-11-03

- Users who already have an email address (including Gmail) should receive their
  administrator-issued temporary GraphiScan password and access link in that inbox.
- Users without email should receive an account identifier and temporary password
  directly from the team. A GraphiScan login identifier does not itself create a
  working mailbox. Providing a real mailbox requires separate mailbox provisioning;
  Gmail account creation is not implemented by GraphiScan.
- All accounts retain mandatory first-password change, followed by explicit privacy
  acceptance and assigned role/record access. A GraphiScan password is separate from
  any mailbox password.
- Local implementation now uses optional Brevo HTTPS delivery after confirmed
  issuance and generates no-inbox IDs for direct handover. A custom domain is not
  required by the adapter. Sender verification/API-key setup, a working public APK
  access link, deployment and actual delivery testing remain open. No invitation
  was actually sent by this implementation session.

## Android release gaps

- No standalone APK/AAB or EAS configuration was found in the searched mobile
  project source. app.json has no android.package; no native Gradle build project
  was found there. These observations do not rule out a build stored elsewhere,
  but there is no recorded standalone release acceptance evidence.
- package.json's export command creates web/Android JavaScript assets. The prior
  Android Hermes export and Expo Go emulator sign-in are not APK installation tests.
- Camera/gallery, image display/sharing, role writes, Back/navigation, process
  restart, keyboard/font scaling and uncertain upload/review recovery require
  installed-app verification. Upload retry identity/form is held in memory;
  navigation/process loss recovery must be exercised before calling it reliable.
- No full hosted teacher -> expert -> parent -> Follow-up execution was recorded.
  Earlier model-disabled/local-unpublished runbook text is historical where newer
  hosting evidence/local commits supersede it; exact deployed revision not checked.

## Checks actually run on 2026-11-03

- Mobile npm run typecheck: passed.
- Mobile npm test: 18 passed.
- Shared hosted client, directory submission and screening submission tests: 19 passed.
- node graphiscan/tools/check_api_contract.cjs: latest614 contract checks and507 isolated
  PostgreSQL checks passed, including review/upload/read authorization, account,
  privacy, password, assignment and Initial/Follow-up constraints. SQL used PGlite
  with fictional records; no hosted service or actual inference was contacted.
- Initial sandboxed backend unittest could not access the base interpreter.
  Approved outside-sandbox execution subsequently passed41 focused account-mail,
  issuance, backend/admin-write and hosted-factory tests using installed Python3.11.9.
  This is mocked account-delivery coverage, not full hosted screening acceptance.
- Final admin build and97 fictional desktop/phone browser assertions passed for
  account delivery. Actual sender/inbox and deployed account-delivery tests remain open.
- Source review: mobile hosted root/onboarding/directory/upload/review/image/report;
  shared tests; predictor; legacy Flask parent filtering; hosted read/write SQL;
  admin expert assignment/review; model evaluation and release records.
- No account, consent, student, review, database, storage or deployment writes;
  no APK generated or physical-device test performed.

## Completion order before defense

Domain payment is pending as of this update. No purchase, DNS change or custom
domain configuration is confirmed. Proposed addresses are graphiscan.site for the
landing page, admin.graphiscan.site for admin, and app.graphiscan.site only if the
user web app is retained; the Android installation page remains /download/.
Domain setup does not block core workflow, native UI or APK development.

1. Use the installed Python runtime with approved access for backend regressions;
   account-delivery focused coverage now passes. The initial sandbox failure does
   not require reinstalling Python.
2. Close the controlled fictional hosted workflow: issued account/gates -> teacher
   student/model/camera-or-gallery upload -> Initial/private image -> admin expert
   assignment -> expert review -> parent released report/image -> Follow-up/history.
3. Verify pending/Flagged/foreign-record denial, reassignment/revocation, retry,
   concurrent Initial protection and failure recovery. Fix demonstrated defects.
4. Configure and build a standalone Android APK; install it and repeat core flows
   against the intended hosted services, including all three model choices.
5. Record device/access/performance results and resolve remaining model/privacy
   and data-migration dependencies. Keep any unfinished gate explicit at defense.

This is an execution priority, not a promise that all gates can be closed by the
deadline. Source coverage and a progress percentage cannot substitute for these
acceptance results.
