# GraphiScan React conversion

Current planning checkpoint (2026-10-22): this conversion already has hosted
onboarding/read/upload/review source. Resume it after the hosted admin action
checks; use `EXPO_PUBLIC_API_MODE=hosted` and the public HTTPS API origin
`https://graphiscan-admin-api.onrender.com` for the next integrated build.
This configuration has not been built/verified in this audit. Current public API
has inference disabled, so online upload screening needs model-capable hosting.
No APK/physical Android release is established. Migrations through019 are already
installed; older unapplied012-015/local-only instructions below are historical.
See `../../CURRENT_REQUIREMENTS.md` for the active order and approval dependencies.

Current hosted checkpoint(2026-10-20): migrations through015 are applied and restricted-read-only preflight verified;3 fictional teacher/expert/parent profiles and separate4-account notice are installed. Admin fresh sign-in/newnotice/synthetic directory check is user-reported successful. Hosted web is running at **http://localhost:5174**(session77508), with EXPO_PUBLIC_API_MODE=hosted and public origin http://127.0.0.1:5002. Root200/bundle/actual login rendering/CORS verified without entering credentials. First complete each role's own temporary-password change, fresh sign-in and explicit notice acceptance; teacher first, then expert/parent. Full populated upload/review/release/device/deployment remains unverified. Do not rerun migrations or use MySQL login for this flow; XAMPP is unnecessary. Older unapplied/setup-pending notes below are historical.

For this web launch: `$env:EXPO_PUBLIC_API_MODE='hosted'`; `$env:EXPO_PUBLIC_HOSTED_API_ORIGIN='http://127.0.0.1:5002'`; then `npm.cmd run web -- --port 5174 --localhost`. Use the localhost frontend address; this launch did not listen on127.0.0.1. The current agent session also uses CI/offline/BROWSER=none, so source changes require a restart. No secret belongs in public Expo variables.

Hosted upload/review/image actions are now implemented in HostedScreeningActions.tsx. They require the prepared, unapplied atomic 013+014 bundle, private Storage, supported pinned artifact and reviewed model/evaluation metadata. Model choices stay unavailable without setup; no synthetic accuracy/default or fallback to legacy credentials is used. See ../api/SCREENING_WRITES.md. Camera/gallery upload, exact-key review retry, request lookup and protected image actions compile, but authenticated hosted/device behavior remains unverified. Admin expert-assignment UI is separate follow-up work.

This Expo/React Native app converts the existing Vue/Capacitor user app in ../user-app. The existing Vue admin remains the admin interface. This directory is a conversion in progress, not a second product or a completed Supabase cutover.

Hosted read integration is now implemented behind EXPO_PUBLIC_API_MODE=hosted with a separate EXPO_PUBLIC_HOSTED_API_ORIGIN. It reuses shared/hosted-client.mjs for sign-in, first-login password change, versioned privacy acceptance, students, results/history/reports and sign-out. It requires the new, currently unapplied migration 012. See ../api/SCREENING_READS.md. Legacy remains the default until hosted write parity is ready; a hosted session never falls back to legacy writes. Suitable issued user-role accounts and a reviewed notice are still required, without broadening the existing admin-only fictional notice.

## Run locally

Use Node 24, run npm ci, then npm run web or npm start. npm run android requires an Android emulator/device and compatible development client. The scaffold uses Expo SDK 58; do not assume an installed older Expo Go supports it.

Copy .env.example to .env.local only if overriding the API origin. EXPO_PUBLIC_API_ORIGIN is a public HTTP(S) origin, with no path, credentials, query or fragment. Android emulator defaults to http://10.0.2.2:5000; other platforms default to http://127.0.0.1:5000. A phone needs a reachable LAN API during development or deployed HTTPS API. Public Expo variables must never contain database passwords, Auth admin keys or private tokens.

## Conversion map

| Existing Vue workflow | React implementation |
| --- | --- |
| Login, forgot/reset password | src/screens/Access.tsx |
| Role dashboards, students, result lists, student history, profile | src/screens/Records.tsx |
| Teacher student creation and parent selection | src/screens/StudentAdd.tsx |
| Teacher sample selection/upload | src/screens/Upload.tsx |
| Teacher/parent result detail, expert validation | src/screens/Result.tsx |
| Authorized handwriting download | src/export-image.ts |
| Existing authenticated API requests | src/core/api.ts |

Navigation exposes teacher, expert and parent workflows. Guest registration/demo is excluded. Sessions stay in memory and require a new sign-in after restart. Server role/ownership rules remain authoritative; client navigation is only presentation. Images are fetched through the authenticated download endpoint, never through a public static URL in this client. Native image sharing uses a temporary cache file, cleaned after the share sheet completes.

The legacy adapter deliberately targets /api/user and legacy identifiers. Supabase bearer sessions/UUIDs must not be passed into that adapter. Hosted mode now integrates v1 onboarding and screening reads; hosted upload/review/image writes remain pending. Legacy password recovery still relies on the development flow; real email delivery and app-link issuance remain to be connected.

Model labels remain Normal and High Potential. Stored legacy scores already use percent units; small values are not multiplied by 100. No clinical probability, AI recommendation, three-model selector or unrecorded screening type is invented. Expert recommendation is entered by the expert, as required by the existing API.

Results, details and dated history display recorded Initial Screening/Follow-up Screening from the reports table through the existing API. Missing, conflicting or unsupported labels show Screening type not recorded. Visible list order never determines the type: a parent's earliest reviewed report can correctly be Follow-up. This read projection does not fix concurrent upload assignment; hosted transactional writes remain pending.

## Verification and remaining work

Run npm run typecheck, npm test and npm run export. Export produces web assets and an Android JavaScript bundle, not an APK or device verification. Camera, permissions, keyboard/back behavior, image sharing, reset links and authenticated role flows require device testing. Launcher artwork is still generated scaffold artwork pending approved branding. History is a dated list; chart/report parity needs review against the retained Vue views. School assignment and panel additions require the hosted API integration rather than fields the legacy API cannot persist.

No upload or other write retries automatically after a failed connection. Check the saved records before repeating an uncertain write. Existing legacy upload storage, process-local sessions and broad CORS handling remain backend migration work before deployment; this conversion does not claim production protections.

Reference: https://docs.expo.dev/get-started/create-a-project/
