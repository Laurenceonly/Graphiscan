# GraphiScan stack and hosting decision

Decision date: 2026-09-29. This is the agreed target architecture for the capstone pilot. It is not a claim that migration, model validation, or deployment is complete. Deployment is a later phase.

## Architecture

`Vue admin (Vercel)` and `React Native mobile (installed on devices)` → `Flask JSON API (Cloud Run)` → `Supabase PostgreSQL + private Storage`.

`Supabase Auth` issues login sessions to both clients. Flask verifies the user token and enforces role, student ownership, first-login password change, and approved privacy agreement acceptance before returning protected data. Flask runs `TensorFlow/Keras` inference and stores the model/version with each result. Clients never hold a server secret key or connect directly to private student tables.

## Stack

| Part | Decision | Current state |
| --- | --- | --- |
| Admin website | Vue 3 + Vite, keep the existing app | Existing admin screens and JavaScript remain useful; no value in rewriting them. |
| Android mobile app | React Native + Expo + TypeScript, built as a native Android app | Current mobile app is Vue 3 + Capacitor; retain it until the new app reaches feature parity. The new app must use release builds for performance decisions, not Expo Go. |
| Backend API | Python + Flask, JSON REST API | Existing role and inference logic is in Flask. Run with a production WSGI server such as Gunicorn on Linux; do not use Flask's debug server in deployment. Do not switch to FastAPI solely for speed. |
| Inference | TensorFlow/Keras behind the Flask API | Production remains binary today. Target is Normal / Low Potential / High Potential using all three validated model families, with the best evaluated model as default and manual model selection. Record model name and version with every screening. |
| Database | Supabase PostgreSQL | Current SQL and connection code use MySQL. Migrate schema and queries deliberately. XAMPP/MySQL are only part of the current local setup, not the target stack. |
| Authentication | Supabase Auth plus Flask authorization | The GraphiScan team (administrator or authorized researcher) creates each account and provides a temporary password. On first login, that user must choose a new password and accept the approved Data Privacy Agreement before accessing features. Supabase Auth manages credentials and sessions; Flask enforces these gates, roles, and student ownership from trusted database records. Current in-memory Flask tokens must be replaced. |
| Image storage | Supabase Storage, private bucket | Current images are saved under Flask static files. Use server-authorized uploads/downloads or short-lived signed URLs; never expose student images through a public bucket. |
| Source control | Private GitHub repository | Store source and safe templates, never credentials, real student data, private models, or raw datasets. |

The target account fields and consent history start in `graphiscan/db/postgres/001_identity.sql`. Applying that migration and connecting it to Supabase Auth and Flask are still pending. A user account must be created through an authorized admin/researcher server action, with `must_change_password = true`. The login flow must allow only password change and agreement acceptance until onboarding is complete. Existing numeric MySQL user IDs will require a reviewed mapping to Supabase Auth UUIDs.

The old MySQL database has eight tables. A schema-only reference was extracted to `graphiscan/db/legacy_mysql_schema.sql` from a local export dated 2026-07-28. It contains no row data, but it may be older than the current XAMPP database. The original export contains private rows and must remain outside Git. `C:\Users\MY_PC\Downloads\CAPSTONE\graphiscan_db` is a separate folder of MySQL/MariaDB `.frm` and `.ibd` table files, not a portable SQL migration. The XAMPP copy of the eight tables has later file timestamps, so use a fresh logical export from the authoritative running database before migrating any rows. Target PostgreSQL table drafts are now in `001_identity.sql` and `002_screening.sql`; neither has been applied, and the import/API conversion remains open. See `graphiscan/db/MIGRATION_NOTES.md` for the table mapping. XAMPP can be retired only after a current backup, PostgreSQL schema/data migration, API conversion, and cutover are complete.

## What must be hosted

| Item | Proposed free-tier service | What gets deployed or stored |
| --- | --- | --- |
| Admin website | Vercel Hobby for the capstone pilot | Built Vue static files. Set project Root Directory to `graphiscan/admin-web`, Build Command to `npm run build`, Output Directory to `dist`, and `VITE_API_ORIGIN` to the production HTTPS API origin. |
| API and model | Google Cloud Run | Container containing Flask, dependencies, and a provisioned model artifact. Set an appropriate memory limit and one model-loading strategy. |
| Database and login | Supabase Free PostgreSQL and Auth | Accounts, students, screenings, validation, consent records, and reports; Auth issues sessions. |
| Private images | Supabase Free Storage | Original handwriting images and access policies. Do not put student samples in public buckets or Git. |
| Mobile app | Expo EAS Free for Android builds; distribute the resulting APK/AAB as appropriate | The app itself is installed on devices and calls the HTTPS API. EAS builds are a build service, not app runtime hosting. Google Play distribution is separate. |
| Source code | Existing private GitHub repository | Source and safe templates only. Never upload real `.env`, credentials, student records/images, raw datasets, or private model artifacts. |

Free subdomains from the hosting services suffice for a pilot; a custom domain is optional. Choose a region near the users where each provider offers one. Keep API credentials only on the server; the mobile and web builds may contain only public endpoint URLs and carefully scoped public keys.

## Free-tier limits and practical decision

- Vercel Hobby can host the Vue/Vite admin app for a personal, non-commercial capstone pilot. Its Hobby plan is restricted to non-commercial personal use. Source: https://vercel.com/docs/plans/hobby
- Cloudflare Pages Free remains an alternative static host if Vercel's Hobby terms do not fit the deployment. It allows 500 builds per month. Source: https://developers.cloudflare.com/pages/platform/limits/
- Supabase Free lists 500 MB database size, 1 GB storage, and 5 GB egress. Inactive free projects can be paused. Sources: https://supabase.com/docs/guides/platform/billing-on-supabase and https://supabase.com/docs/guides/platform/free-project-pausing
- Cloud Run has a monthly free allowance, but requires a Google Cloud billing account and charges beyond allowance. A cold start and TensorFlow model load could exceed the manuscript's 5-second response target. Measure this before a live demonstration. Sources: https://cloud.google.com/run/pricing and https://docs.cloud.google.com/docs/get-started/learn-about-billing
- If a billing account is unavailable, Render Free is a temporary API demo option. It sleeps after 15 minutes without traffic, may take about a minute to wake, and loses local files on restart, so it cannot meet a reliable 5-second target. Source: https://render.com/docs/free
- Expo EAS Free has limited monthly Android builds. Source: https://expo.dev/pricing

These free tiers are a capstone pilot plan, not a guarantee of zero cost, uptime, or suitability for real student records. Before collecting real student data, review consent, access, retention, backups, and the hosting providers' terms with the school. A production service may need a paid tier.

## Why React Native with Expo instead of Flutter

- Both can produce smooth native Android and iOS apps. React Native renders platform views; Flutter draws its own widgets with its rendering engine. Neither guarantees smoothness on an underpowered phone or a slow API.
- React Native lets the team keep using JavaScript concepts from Vue, while learning React and TypeScript. Flutter would require learning Dart and a second UI ecosystem during the same database, auth, and model migration. This is a project-delivery decision, not a claim that Flutter is inferior.
- Expo simplifies camera/image picker, permissions, Android builds, and device iteration. An Expo app is a React Native native app, not a WebView. For real development use a development build; Expo Go is only a limited playground. Release builds must be assessed on target devices.
- Flutter is a strong alternative if the team already knows Dart or needs highly custom, consistent graphics. For GraphiScan's forms, image capture, reports, and charts, React Native's native views are sufficient if implemented carefully.

Sources: https://reactnative.dev/docs/performance, https://docs.expo.dev/workflow/overview/, https://docs.flutter.dev/resources/architectural-overview, https://docs.flutter.dev/perf/ui-performance

## What this decision does not promise

- A fast mobile UI does not make TensorFlow inference or a sleeping free-tier backend fast. The manuscript's five-second result target needs release-build and hosted-API measurements.
- Supabase Free can pause for low activity and Cloud Run can cold start. Cloud Run needs billing enabled; staying inside its allowance is a usage goal, not a guaranteed zero bill.
- The three-class model is a target. Do not call the existing binary model three-class or present its 86.03% result as a three-class result.

## Deployment sequence

1. Finish the data model and migrate MySQL queries/data to PostgreSQL with a reviewed migration and backup plan.
2. Replace local static uploads with a private storage flow; enforce server-side authorization for every image and record.
3. Implement team-issued temporary accounts, a server-enforced first-login password change, approved privacy agreement acceptance, and durable authentication. Never store or send temporary passwords in Git or application logs.
4. Finalize and validate the three-class model registry and screening semantics; package model artifacts outside Git.
5. Deploy the API and database, then the admin site, then the Expo app using environment-specific HTTPS API URLs.
6. Measure real-device upload, model startup, response time, and free-tier usage before calling the deployment ready.
