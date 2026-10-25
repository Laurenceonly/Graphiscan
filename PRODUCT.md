# GraphiScan product

<!-- impeccable:product-schema 1 -->

## Platform

android

## Scope

This design brief applies to the Expo user application in `graphiscan/mobile-app`.
The Vue admin website is a separate retained web surface. The Vue user application
is a workflow reference, not the native implementation.

## Users

Teachers capture and organize elementary students' handwriting screenings.
Experts review assigned screening records and provide their own remarks.
Parents and guardians read released reports for their linked children. All three
roles belong in the native application; administration remains on the web.

## Product Purpose

Connect handwriting samples, model screening output, expert review and subsequent
history without presenting screening as a diagnosis. The school/grade scope is
Grades1–3. Accounts are issued, with password and privacy gates before features.

## Operating Context

An Android phone is the primary native target. The app uses React Native/Expo,
React Navigation and the shared hosted client. Public HTTPS API requests reach
the Flask service backed by Supabase Auth/PostgreSQL/private Storage.

## Capabilities and Constraints

- Server role, ownership, onboarding, school scope and report-release checks remain
  authoritative. Client presentation cannot grant access.
- Required password change leads to fresh sign-in; privacy uses the exact current
  server version and explicit acceptance. The real-use policy is not yet approved.
- Current Render hosting has inference disabled. Do not promise working online
  screening, model availability, new model accuracy or a diagnostic outcome.
- Preserve recorded binary classifications and Initial/Follow-up history.
- Hosted student creation/editing and school/grade filters are implemented in
  source. Remaining feature parity, native/hosted checks and an APK release remain open.
- Browser rendering is an engineering aid, not native release evidence.

## Brand Commitments

User direction2026-10-25: extend the admin's steel blue #355c8c branding and slate
surfaces to Expo, including the logo and Scan wordmark. Use muted blue #45638a
for shared light controls and lighter accents in dark mode for readability.
This supersedes the earlier supplied-logo royal-blue color choice, while retaining
the supplied logo shape, native layout and functional behavior.

Logo selection2026-10-25: user supplied Glossy Interlocking Blue G-S Logo.png and
requested it across admin and Expo. Preserve its glossy blue artwork without
recoloring filters. Keep the steel blue/slate interface and matching Scan lettering.

Retain GraphiScan's name, supplied logo and recognizable blue identity. The user
requested a professional, appealing native interface, consistent alignment and
spacing, concise wording, no redundant controls and no generic AI decoration.
The user reconfirmed white and blue, clean and professional; avoid ornamental styling.
The user explicitly chose building directly in Expo rather than image mockups.
The supplied Dribbble login search guides authentication; the mobile UI search
guides the remaining screens. Feed-style skeleton loading is requested for data
loads, with restrained motion and an accessible static alternative.

## Evidence on Hand

`KNOWLEDGE.md`, `CURRENT_REQUIREMENTS.md` and `CHANGELOG.md` record observed source,
hosted checks and unresolved release gates. `graphiscan/user-app/src` supplies the
existing role workflows. Existing logo assets ship with the Expo application.
Only clearly fictional data may be used for design previews. Real credentials
and student records must never be committed or used as decorative content.

## Product Principles

- Make the next role-appropriate task easy to find.
- Keep model output and human review distinct and accurately attributed.
- Preserve familiar native navigation and form behavior.
- Reuse one visual vocabulary across roles, with truthful empty/loading/error states.
