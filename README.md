# GraphiScan

GraphiScan is a capstone project that explores how image classification can support handwriting screening for possible dysgraphia-related difficulties. It is designed as a **screening aid**, with expert review of results, and is not a clinical diagnosis.

## Project overview

Teachers can manage student records and submit handwriting samples for screening. The application records the model result, supports expert validation, and presents reviewed information to authorized users. A separate admin interface supports account and record management.

## Built with

- **Application:** Flask API, Vue 3 interfaces built with Vite, and an in-progress React Native/Expo app.
- **Machine learning:** TensorFlow/Keras and image preprocessing in Python.
- **Data:** The legacy prototype uses MySQL. The Supabase Auth/PostgreSQL v1 schema is installed through migration019; full legacy-data migration and application cutover remain in progress.
- **Mobile:** React Native/Expo is the agreed native direction; the existing Vue/Capacitor client remains until role and device parity are verified.

## Current status

The [admin pilot](https://graphiscan-admin.vercel.app/login) is published on Vercel
with a lightweight Flask API on Render Free and existing Supabase Auth/PostgreSQL/
private Storage. Hosted admin login/dashboard is user-confirmed. Account-action
source is implemented and migrations through019 passed restricted read-only
verification; complete hosted action and role workflows still need verification.
Model inference is disabled on this admin-only API. Free model hosting,
three-class evaluation, Expo APK/device checks, legacy-data/image cutover and
manuscript/privacy approval remain open. See [current requirements and next
steps](CURRENT_REQUIREMENTS.md) and [hosting details](graphiscan/api/HOSTING.md).

## Responsible use

Model scores are screening outputs, not medical conclusions. A qualified expert should review results before they are shared. Student records and handwriting images require restricted access and must not be placed in a public repository or public storage bucket.
