# GraphiScan user app

Hosted account onboarding is available at `/access`, linked from `/login`, for
teacher/expert/parent accounts. It uses shared v1 login/refresh/password/privacy/
logout with in-memory tokens and no legacy token fallback. Reload requires
sign-in. Reviewed migration 008 is needed for durable sign-out; student/result
screens remain on MySQL until resource migration. See
[session integration](../api/SESSION_INTEGRATION.md). This is web onboarding,
not Expo/native persistence or full resource cutover.

Vue 3 mobile interface for teachers, parents, experts, and guests, packaged for Android with Capacitor. Start the Flask backend from `graphiscan/`, then run `npm install` and `npm run dev` in this directory. Set `VITE_API_ORIGIN` in a local `.env` using `.env.example`; use a backend address reachable from the device. The Android project remains in `android/`.
