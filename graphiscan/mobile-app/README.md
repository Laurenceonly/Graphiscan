# GraphiScan Expo application

Branding2026-10-25: steel blue #355c8c actions/wordmark accents, muted blue controls
and neutral slate surfaces match the revised admin. Dark mode uses lighter blue
interactive/wordmark accents. Shared BrandLogo renders the user's Glossy
Interlocking Blue G-S Logo.png directly in login, Home and onboarding. app.json
uses the same asset for the app/adaptive icon and web favicon; installed launcher
icons need a new native build. This source change is local, not an APK release.

The native Android conversion lives here. `../user-app` is the Vue reference for
teacher, expert and parent behavior; `../admin-web` remains the web admin.

## Current integration

Hosted mode is now the default and uses the public API at
`https://graphiscan-admin-api.onrender.com`. No local MySQL server is required.
Only an explicit `EXPO_PUBLIC_API_MODE=legacy` selects the archival adapter.
A hosted session never falls back to legacy endpoints.

| Flow | Current source |
| --- | --- |
| Sign-in | Issued teacher, expert and parent accounts; branded native login |
| Required password change | Server gate, confirmation, private visibility controls and fresh sign-in after success |
| Privacy agreement | Exact server-published version/content, explicit consent, reload on a changed agreement; no bundled substitute policy |
| Home | Role-specific actions and counts of loaded records, capped at the requested page size |
| Students / Children | Server search and school/grade filters, scoped paging and screening history; teacher-only Add/Edit using the hosted API |
| Results / Reviews / Reports | Scoped lists, model metadata, expert review, private image and released-report actions |
| Teacher screening | Existing camera/gallery upload and model selection source; online inference is disabled on the current Render service |
| Profile | Account refresh and sign-out |

Shared spacing, typography and controls live in `src/ui.tsx`; record rows,
selection rows and branding live in `src/WorkspaceUI.tsx`. `src/HostedHome.tsx`
provides role actions/recent records. `src/LoadingSkeleton.tsx` supplies initial
student, screening, detail and agreement placeholders with a restrained opacity
pulse. Reduced-motion, background and unfocused states use static placeholders;
existing content stays visible during refresh. Motion uses the SDK-compatible
Reanimated/Worklets dependencies; no artificial request delay is added.
Onboarding uses `src/AccountSetup.tsx`; hosted navigation/read flows live in
`src/HostedApp.tsx`. Tokens remain in memory and restart requires sign-in.
Server role, ownership, onboarding and release rules remain authoritative.
No credential or consent write automatically replays after a failed connection.

Hosted directory source lives in `HostedStudents.tsx`, `HostedStudentEditor.tsx`
and `HostedDirectoryControls.tsx`. School/parent options are scoped API reads.
Teachers cannot choose a different teacher or move a student's school. Creates
retain the same key/body in memory after an uncertain response; fields and
navigation stay locked for explicit retry. An uncertain edit or revision conflict
requires a current-record reload. Restart/sign-out loses the in-memory form;
check existing students before starting another creation after losing that state.
These paths have fictional browser/local SQL evidence, not real hosted/device proof.

## Open on Android

Android Studio's built-in Android Emulator is supported. On this computer,
`GraphiScan_Pixel_6` is an Android 16 (API36), Google APIs x86_64 virtual phone.
Open it from Android Studio's Device Manager before starting the preview.
The matching Expo Go58.0.5 client is installed; this is development testing,
not a standalone GraphiScan APK.

For the local emulator, run from `graphiscan/mobile-app`:

```powershell
npm.cmd run preview:android
```

This launcher opens Expo Go through port8081 and uses IPv4-first localhost
resolution so Android's `adb reverse` can reach Metro on Windows. It discovers
the default Windows SDK when `ANDROID_HOME` is unset. The existing hosted HTTPS
API default is retained; this launcher does not enable the browser-only proxy.
Verified Metro's IPv4 status returned HTTP200 after reproducing an IPv6-only
listener that prevented Expo Go from downloading the development project.

For a physical phone on the development network:

From the repository root, run:

```powershell
Set-Location .\graphiscan\mobile-app
npm.cmd start -- --lan
```

Open the development session on the phone using a native client compatible with
this project's installed Expo SDK58, or use an Android emulator. The phone must
reach Metro on the development computer. The API itself already uses public
HTTPS. An incompatible Expo Go version requires a compatible native client;
this source change does not generate one.

Optional public overrides are documented in `.env.example`. Do not put database
passwords, Auth administrator keys or private tokens into `EXPO_PUBLIC_*` values.
The hosted default works without an environment file. The legacy origin setting
is used only by the explicit legacy adapter.

## Evidence and remaining work

Logout/loading follow-up2026-10-23: manual sign-out opens a shared confirmation
dialog in hosted/legacy profiles, account setup and pending student forms. Cancel,
Escape or Android Back close the dialog; Confirm uses the existing logout action.
Automatic expiry/recovery still closes sessions without prompting. Pending forms
explain recovery loss before confirmation.

Feed-style initial loading now covers lists/history/details/agreement plus
student/model choices, schools, eligible parents, student headings and private
images. Same-query refresh keeps loaded content; changing query/record removes
the old scope's content until the new response. Save/sign-in/upload progress
labels remain action states. Motion and reduced-motion/lifecycle fallback are
unchanged. TypeScript,18 mobile/19 shared tests,14 fictional browser cases and
Android export1296 modules passed. Native dialog/Back and legacy MySQL runtime
checks remain separate; no actual logout/record write ran in this follow-up.

Native checkpoint2026-10-23: the API36 emulator booted, Expo Go58.0.5 loaded
GraphiScan, and login captures were inspected in light/dark and at dark font
scale1.3. An actual keyboard overlap was fixed by Android height behavior in
SignInPanel and shared Screen; the recapture keeps password/sign-in above IME.
Normal text/light mode was restored. Final TypeScript and Android Hermes export
passed1295 modules/19 assets/3.4MB;18 mobile/19 shared tests and11 fictional
browser directory checks also passed in this continuation. Native role and
hosted role verification remain pending; automated checks did not submit credentials.
The user subsequently confirmed successful private emulator sign-in after a wait.
Public health then returned200 in1.31s and emulator DNS/ping succeeded; the
original sign-in latency/cause was not captured. Full onboarding/role/write flows
are separate checks.

Observed development limitation: changing Android font scale triggered an
Expo Go automatic-reload runtime EventEmitter failure in expo-modules-core.
A fresh Expo Go process recovered. The underlying cause and behavior in a
standalone native build are unverified; configuration-change reliability remains
open. Preserve any pending write recovery state before restarting the app.

### Browser layout preview

For an engineering preview on this computer, run `npm.cmd run preview` and open
`http://localhost:5174`. This command enables a local Metro proxy restricted to
the configured GraphiScan public `/api/v1/` API. It forwards required bearer/body
headers without logging or retaining them. Native builds keep calling the public
HTTPS origin directly; production browser-origin settings stay unchanged.
Use the localhost address consistently and refresh after restarting Metro.
On a desktop viewport wider than600px, this development-only preview centers a
420px app canvas. Native builds fill the device. Root `DESIGN.md` documents this
Expo design system; it does not replace the Vue admin's design.


On2026-10-22, TypeScript checking and Android JavaScript/Hermes export passed.
This produces a bundle, **not an APK**. Fictional browser layout review is an
engineering aid; it is not Android device, camera, keyboard or authentication
verification. No real passwords, consents, reviews or student records were changed
by that preview. The local SDK is present; no Android device was connected at the
latest check.

Before native release:

- Complete issued-user onboarding and scoped teacher/expert/parent flows on a
  physical Android device, including font scaling, keyboard, back navigation,
  network failure, sign-out, private image sharing and camera permissions.
- Keep the current fictional privacy audience intact. Approved real-use agreement
  publication and account audience setup are still separate dependencies.
- Verify hosted assignment, report release and expert review with authorized
  accounts. Hosted student-creation/editing and school/grade filtering are now
  implemented in source; verify them on Android and against authorized hosted
  records. Full Vue feature parity remains open; the old creation screen is
  used only by the explicitly selected legacy adapter.
- Enable a reviewed model-capable backend before claiming online handwriting
  screening. Preserve recorded binary classes and model scores; do not invent a
  Low Potential class, diagnosis or accuracy figure.
- Produce and verify an Android APK. Historical data/image migration and final
  manuscript evidence remain tracked in `../../CURRENT_REQUIREMENTS.md`.

The existing `typecheck`, `test` and `export` scripts remain available. The latest
2026-10-23 follow-up passed18 mobile/19 shared tests, TypeScript, Android export
and25 combined fictional browser views/workflows. This supersedes earlier notes
that a UI-only slice did not run the unit suite.
