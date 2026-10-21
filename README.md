# GraphiScan

GraphiScan is a capstone project that explores how image classification can support handwriting screening for possible dysgraphia-related difficulties. It is designed as a **screening aid**, with expert review of results, and is not a clinical diagnosis.

## Project overview

Teachers can manage student records and submit handwriting samples for screening. The application records the model result, supports expert validation, and presents reviewed information to authorized users. A separate admin interface supports account and record management.

## Built with

- **Application:** Flask API, Vue 3 interfaces built with Vite, and an in-progress React Native/Expo app.
- **Machine learning:** TensorFlow/Keras and image preprocessing in Python.
- **Data:** The legacy prototype uses MySQL. The Supabase Auth/PostgreSQL v1 schema is installed through migration017; full legacy-data migration and application cutover remain in progress.
- **Mobile:** React Native/Expo is the agreed native direction; the existing Vue/Capacitor client remains until role and device parity are verified.

## Current status

GraphiScan is in active development. Supabase migrations through017 and the separate admin writer are installed and passed restricted read-only verification. Guarded account updates are implemented; actual mutation flows still need hosted verification. Account issuance/password reset, legacy-data/image migration, populated role-flow verification, final model decisions and deployment remain open. The user requires free model hosting; provider selection is pending. See [hosting preparation](graphiscan/api/HOSTING.md). A public link will be added after deployment.

## Responsible use

Model scores are screening outputs, not medical conclusions. A qualified expert should review results before they are shared. Student records and handwriting images require restricted access and must not be placed in a public repository or public storage bucket.
