# GraphiScan Expo application

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
| Students / Children | Scoped list and screening history |
| Results / Reviews / Reports | Scoped lists, model metadata, expert review, private image and released-report actions |
| Teacher screening | Existing camera/gallery upload and model selection source; online inference is disabled on the current Render service |
| Profile | Account refresh and sign-out |

Shared spacing, typography, control heights and list rows live in `src/ui.tsx`.
Onboarding uses `src/AccountSetup.tsx`; hosted navigation/read flows live in
`src/HostedApp.tsx`. Tokens remain in memory and restart requires sign-in.
Server role, ownership, onboarding and release rules remain authoritative.
No credential or consent write automatically replays after a failed connection.

## Open on Android

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
  accounts. New hosted student-creation UI and full Vue feature parity remain
  follow-up work; the old creation screen still targets the legacy API.
- Enable a reviewed model-capable backend before claiming online handwriting
  screening. Preserve recorded binary classes and model scores; do not invent a
  Low Potential class, diagnosis or accuracy figure.
- Produce and verify an Android APK. Historical data/image migration and final
  manuscript evidence remain tracked in `../../CURRENT_REQUIREMENTS.md`.

The existing `typecheck`, `test` and `export` scripts remain available. The test
suite was not run in this UI/integration session.
