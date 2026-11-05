# Initial software flow and UI verification

Follow-up2026-11-03: the later supporting-page fixes supersede earlier justified
copy and stacked footer notes: long text uses natural left alignment, short mobile
introductions center and the footer stays in one row. Password setup has no lock
decoration/repeated sign-in note. Admin's eight-section cleanup review passed74
checks at7 widths using fictional responses. The mobile app now uses a full white
canvas/light palette (including dark OS preference) without an enclosing setup
card;53 fixed-export browser checks passed across teacher/expert/parent and the
ordered password/privacy flow. Temporary onboarding is for those mobile roles.
Admin/researcher permanent issuance/reset behavior is prepared in unapplied022;
66 focused mocked Python tests and614 contract/532 isolated SQL checks passed.
These remain local changes, with no hosted migration, real credentials or native
APK/device acceptance established by these checks.

Date: 2026-11-03. Defense: November11. Paper/deck work remains deferred.

**Initial local browser flow/layout review is complete. This is not signed-APK
acceptance or a completed hosted teacher/expert/parent workflow.**

## Results and boundaries

| Surface/check | What ran | Result |
| --- | --- | --- |
| Stateful role flow |77 checks and41 captures, using intercepted fictional API responses | Passed; zero application page errors |
| Public website |216 checks across Home/About/Data use/Download and8 viewports | Passed; no recorded overflow, heading/action clipping or page errors |
| Admin |All8 sections across7 viewports, plus dialogs, history, password fields, delayed navigation, retry, drawer and logout cancel;74 recorded checks | Passed; no recorded issues or application page errors |
| Results/history recovery |Actual current mobile component against simulated failed reads | Try again recovers both lists successfully |
| Download short-copy spacing |17 focused checks after the correction | Passed; short release copy is left-aligned, longer supporting copy retains its earlier alignment |
| Remove public admin entry |36 checks across all4 public pages at320/768/1440 | Passed; no admin entry anchors,3 public footer links retained, no document overflow |
| Public navigation after cleanup |About/Data use/Download clicks, Back and curtain recovery | All3 route pairs passed |
| Build/export |Strict landing build; mobile Android and web export | Passed; Android output is a Hermes asset bundle, not an installable APK |
| Export origin check |Scanned both exported bundles | Public Render API present; localhost fixture origins absent |
| Native runtime attempt |Installed Pixel6/API36 emulator and Expo Go development launch | Incomplete: ADB shell/reverse/package operations timed out; no new native UI captures accepted |

The earlier same-session89 combined Python workflow/access tests,18 mobile tests,
19 shared-client/submission tests,614 contract checks and507 isolated SQL checks
are recorded in CHANGELOG.md. Those use synthetic fixtures/mocks/PGlite; they do
not establish actual hosted Auth, inference, private Storage or physical-device
behavior. Intentional simulated503/404 responses appear in browser network logs;
they are separate from application JavaScript page errors.

## Flow exercised in the browser

1. Required password change rejects mismatched confirmation; one successful
   submission returns to sign-in.
2. The current fictional agreement loads and requires explicit acceptance.
3. Teacher selects an assigned fictional student and sees all3 model choices.
   Explicit ResNet50 selection is preserved on the saved fictional result.
4. A deliberately uncertain upload response is retried with the same key,
   preserving one Initial Screening record.
5. Admin assigns the expert through the actual Vue assignment controls.
6. The assigned expert validates with separately attributed human remarks.
7. Parent sees no Pending record, then sees the released result/report/image.
8. A second upload using EfficientNetB0 is recorded as Follow-up Screening.
9. A later Flagged review hides the Initial record from the parent. The remaining
   visible record/history retains Follow-up; it is not relabeled by list order.
10. Denied detail refresh clears the displayed image and report action. Rapid
    delayed navigation does not expose results in the student view.

These are real client interactions with a stateful fake API. The fake API's
authorization behavior is not server-security proof; the separate SQL/runtime
tests cover the source rules within their own stated limits.

## Layout coverage

Public site:
320x568,360x800,390x844,568x320,768x1024,1024x768,1366x768,1920x1080.
Checked menus/Escape, workflow/role selectors, FAQ, headings, footer bounds,
control-label fit and the disabled unreleased APK state.

Admin:
1920/1440/1024/768/390/320 widths at900px height, plus568x320 landscape.
Covered Dashboard, Users, Students, Schools, Results, Progress, Audit Logs and
Settings. Drawers were allowed to finish closing before final captures. Earlier
mid-transition images were audit timing artifacts, not accepted settled layouts.

User components:
Teacher/expert/parent home, records, detail and history at320 light,390 dark and
768 light/reduced motion, plus upload/review/onboarding at390. The development
web preview uses a phone canvas above600px: its768px results are not native
Android tablet evidence.

Selected desktop/phone captures were visually inspected. Captures and browser
scripts live under ignored output/playwright and .local-tools; no real learner
images or records were used. The public landing keeps its established imagery
and typography; admin/native component presentation keeps its blue/slate identity.

## Corrections made

- Added visible Try again to failed Results/history reads using existing refresh.
- Corrected NumPy test isolation so compiled modules remain cached when removing
  mocked predictors; the combined Python suite passes.
- Fixed stretched short Download introduction/release text at narrow widths.
- At the user's request, removed Admin portal anchors from all public HTML pages,
  their runtime URL injection/configuration and obsolete transition handling.
  The admin remains independently accessible on its subdomain.

Test harness corrections were also required for hidden retained navigation
screens, changing menu labels, current Settings button wording and viewport
changes across the development canvas breakpoint. A premature missing-retry
result was caused by reading the old hidden Home error while Results was loading.
It was not evidence that the completed source fix failed or that caching alone
caused the failure.

## Still required before calling the app complete

- Build/sign/install the standalone APK and repeat the core role flow.
- Native phone/landscape/tablet classes as supported, camera/gallery, sharing,
  keyboard/insets, larger system fonts, Back gestures, restart and recovery.
  The emulator launched for this attempt was closed after its ADB timeouts.
- Actual hosted private test-account sign-ins and teacher upload -> assignment ->
  review -> parent release -> Follow-up, with real private-image authorization,
  denial/revocation, retries and concurrent Initial protection.
- All3 hosted model choices, measured response time/reliability, approved real-use
  privacy and the remaining model/historical-data requirements in the defense audit.
- Publish the reviewed source before claiming these local UI changes are live.

Finite viewport checks do not guarantee every screen/browser/font/device. No
screen-reader certification, frame-rate guarantee, clinical/model validation or
full production acceptance follows from this initial review.
