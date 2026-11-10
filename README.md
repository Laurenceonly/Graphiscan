# GraphiScan

GraphiScan is a capstone project that explores how image classification can support handwriting screening for possible dysgraphia-related difficulties. It is designed as a **screening aid**, with expert review of results, and is not a clinical diagnosis.

## Project overview

Teachers can manage student records and submit handwriting samples for screening. The application records the model result, supports expert validation, and presents reviewed information to authorized users. A separate admin interface supports account and record management.

## Built with

- **Application:** Python/Flask API, Vue 3 admin web interface, and React Native/Expo mobile app.
- **Machine learning:** TensorFlow/Keras for model preparation and LiteRT for the hosted model runtime.
- **Data:** Supabase Auth, PostgreSQL and private Storage for the hosted system. A legacy MySQL/Flask/Vue prototype also remains in the repository.

## Current status

The Android 1.0.2 APK and admin website were published on 9 November 2026.
Subsequent mobile and final-report changes are local and have not been published
in a new APK. The user reports that migration 031 passed its three preflight
checks; parent-account acceptance still needs an end-to-end check. The system's
current model labels are Normal and High Potential. For current details and
verification limits, see [KNOWLEDGE.md](KNOWLEDGE.md), [CHANGELOG.md](CHANGELOG.md),
and [the simple system flow](SYSTEM_FLOW.md).

## Responsible use

Model scores are screening outputs, not medical conclusions. A qualified expert should review results before they are shared. Student records and handwriting images require restricted access and must not be placed in a public repository or public storage bucket.
