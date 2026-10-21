# Hosted sessions and client onboarding slice

Implemented locally on 2026-10-20. This slice connects a hosted account to an
actual Vue onboarding screen in both apps. It does not migrate student/result
resources or map Supabase UUIDs onto legacy numeric MySQL accounts.

## API and permission boundary

- `POST /api/v1/session/login` accepts only email/password. The server exchanges
  credentials with the trusted Auth project, verifies the exact returned bearer,
  then loads the current issued active profile before returning only access token,
  refresh token, token type and expiry. Onboarding may still be pending.
- `POST /api/v1/session/refresh` accepts only the refresh token, rotates through
  Auth, then rechecks verified identity/current access. Pending credential writes,
  durable revocations, disabled/unissued profiles cannot regain application
  access by refreshing. Rejected/malformed issued sessions are cleaned up through
  provider-local sign-out where a usable token is available. Cleanup failure is
  not treated as proof of provider revocation.
- Invalid credentials return a fixed 401, provider rate limits a fixed 429 and
  unavailable trusted services 503. Redirects/free-text provider errors are not
  forwarded; credentials and request bodies must not be logged.
- `POST /api/v1/session/logout` verifies the bearer but bypasses account/password/
  privacy availability gates so disabled/onboarding users can leave. Installed
  **008_session_logout.sql** grants the existing restricted writer one definer
  capability to commit a subject-bound session revocation/audit before provider
  local sign-out. No new role/password or direct table/Auth grants are needed.
  Provider failure returns `PROVIDER_SIGNOUT_PENDING`; API revocation has already
  committed. An uncertain DB commit prevents the remote operation and returns an
  error. Local client state is cleared even on transport/remote failure; a failed
  response is not a claim that every provider operation completed.
- Revocation affects only the supplied current session. Other valid sessions
  remain valid. Repetition does not duplicate the audit. A profile/security change
  continues to use the existing broader session-invalidation trigger.

The contract now specifies **33 operations**, eight marked `foundation`. Existing
resource operations remain proposed. The server still checks trusted state on
protected requests; client visibility is not record authorization.

## Vue flow

Open `/access` in either existing app. A link on each existing `/login` screen
opens it; the old login/dashboard flow remains available. The shared
`graphiscan/shared/HostedAccess.vue` handles sign-in, forced-password replacement,
required fresh sign-in, notice display/explicit checkbox acceptance, changed-
version reload and account-setup completion. Admin/researcher accounts use the
admin app; teacher/expert/parent accounts use the user app. Guest was not added to
this new flow; its actual removal from older code remains separately planned.

Passwords are cleared after submissions. Access/refresh tokens live only in the
shared client's memory closure, never localStorage/sessionStorage/cookies or
URLs. Reloading requires sign-in again. Refresh calls are shared per client; a
read may retry once after a 401, but password/consent writes are never replayed.
Generation checks prevent late login/refresh responses from resurrecting logout.
Sign-out clears local state even when the server/provider fails. Native secure
session persistence and multi-tab/multi-device concurrency need separate work.

After onboarding, the screen states truthfully that student/screening records
are not available in this new workspace yet. It does not send a hosted bearer to
legacy resource APIs or silently switch to an old MySQL identity. Resource API
migration is the next dependent slice; this is not a full authentication cutover.

`VITE_HOSTED_API_ORIGIN` optionally selects a separate public origin for this
flow; it falls back to the existing public `VITE_API_ORIGIN`. Ignored local
`.env.local` files now point the two `/access` wrappers to `http://127.0.0.1:5002`.
The existing record clients remain on their original origin/port 5000. No secret
is placed in either Vite variable. Live wrapper-module checks confirmed this
selection; CORS preflights allow both local app origins. Port 5002 health returned
200, empty login/refresh returned 422 and missing-bearer logout returned 401,
without using credentials or changing hosted records. Existing API health on
port 5000 also returned 200.

Both Vite configs deduplicate Vue/vue-router to resolve the shared component to
each app's installed dependencies. The two production builds and both dev routes/
wrapper/shared-module HTTP requests passed. Browser connector inventory was
unavailable for independent visual/interactive QA. User confirmed admin sign-in
displayed Account setup complete and sign-out returned to the sign-in form
without an error. Refresh, revoked-token replay and first-change/privacy-form
interaction in this UI remain separate checks. User reported 008 applied;
all seven hosted read-only function security/grant checks passed.

## Next disposable hosted step

User reported **008_session_logout.sql applied** in the same disposable project;
seven read-only catalog checks independently verified its security/grants.
Do not repeat migrations, seeds or password setup. The migration
does not change any provider session or create acceptance. The currently seeded
fictional Auth account has already completed password and test-notice acceptance.
The user has now confirmed admin `/access` sign-in/readiness/sign-out with the
current privately saved Auth password. Future sign-ins must not use a
database reader/writer password. Never share returned credentials, tokens or
private profile/record details in chat.

The port-5000 listener continued serving old session-route 404s after verified
listener-stop attempts; a fresh app import independently registered the routes
and returned 422 for empty login. The updated API was therefore started separately
on 5002 and verified live as above, preserving the existing workspace origin.
Some old process-local MySQL sessions may need sign-in after restart attempts.
Both frontends and the local hosted API remain running. The earlier stale 404s
do not describe the currently selected hosted origin.

## Evidence and limits

Passing local checks: **129 Python tests, seven browser-client tests, 494 contract
checks and 165 isolated SQL checks**, plus both Vue builds. The SQL suite executes
14 new revocation cases in fictional PGlite; Python provider/driver tests are
mocked. The Impeccable detector returned no findings on the changed Vue files.
These local tests do not establish real provider refresh/concurrency,
network-failure recovery, visual accessibility certification or resource cutover.

Primary technical references reviewed 2026-10-20:
[Supabase Auth REST specification](https://github.com/supabase/auth/blob/master/openapi.yaml),
[Vite shared dependency resolution](https://vite.dev/config/shared-options#resolve-dedupe).
