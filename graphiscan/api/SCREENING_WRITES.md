# Hosted upload and expert-review integration

2026-10-20 admin UI checkpoint: existing Vue admin `/access` now connects scoped screening list/detail, private images and expert-assignment PATCH. Options come from the student's current school and existing actor-specific eligible-person capability, filtered to experts with cursor pagination. Screening revision is submitted; failed/uncertain/conflicting saves require explicit detail reload. No automatic write replay or new permissions/notice audience. Both Vue builds/17 shared-client tests and fictional intercepted browser checks passed; real populated hosted assignment remains unverified. This supersedes the older admin-UI-pending notes below. See admin-web/README.md and tools/check_hosted_admin_browser.js. Rough overall53%.

The user reported the atomic 013+014 bundle applied on 2026-10-20. All 19 restricted hosted read-only metadata/privilege/nonexistent-identity checks passed. Updated local API5002 serves health200 and six new protected route probes401/no-store without authentication. Do not repeat the bundle. Storage settings are saved and bucket metadata/list read checks passed; privacy and object writes remain unverified. Model manifest/publication, user-role accounts/privacy and authenticated device verification remain prerequisites. These features are not deployed.

## Apply one atomic bundle

Already applied and metadata-verified: ../db/postgres/013_014_screening_writes.sql. For a fresh project only, run this bundle once after 001–012. This tested bundle wraps both source migrations in one transaction: a failure rolls everything back. Do not run 013 and 014 separately as well, or repeat earlier migrations. It adds fixed-path function capabilities to the existing reader/writer and a private upload-intent table. No accounts, model/evaluation rows, user permissions, application records, buckets or credentials are seeded. The existing function-only writer password is reused.

After user-reported success, run tools/check_v1_screening_writes.py --connect through the existing restricted reader. It checks catalogue permissions and nonexistent-identity read denials, never invokes write/cleanup functions. Restart the local API only after verification. This is not a populated authorized write test.

## Multipart parser correction — 2026-10-24

The upload route allows128KiB multipart parser buffering and separately rejects
text-field values above16KiB. The prior16KiB decoder limit rejected ordinary
photos when Werkzeug supplied a64KiB chunk. Image limits remain10MiB input and
normalized output,16MP and one frame. Generated PNG/JPEG and exact/over10MiB
regressions reproduce the old413;35 isolated upload/hosted/model tests pass after
the fix. Hosted deployment and the actual role workflow remain unverified.

## Implemented routes and behavior

- GET /models: bounded metadata, signed pagination, effective selectable/default flags. Models absent from the configured runtime or lacking private Storage are not offered as selectable. No artifact paths, weights or guessed evidence are returned.
- POST /screenings: teacher-only multipart student_id, optional model_id, handwriting_image and required Idempotency-Key. Positive identifiers and exact allowlists are checked; real image format, byte size and decoded pixels are bounded. JPG/PNG is normalized to one RGB PNG with EXIF orientation applied and metadata removed. Current configurable-code baseline is 10 MiB input/normalized output, 16 megapixels, one frame; these are initial limits, not a measured device/latency guarantee.
- GET /screening-requests/{idempotency_key}: submitting actor's durable state, current ownership and completed-result scope. Never expose another actor's request, private object path or original payload.
- PATCH /screenings/{result_id}/review: currently assigned expert only, required human remarks, optional human recommendation, boolean follow-up flag, review expected_revision and required idempotency key. Immutable history/audit and reviewer/date are server generated. A Flagged review withdraws subsequent parent result/report/image access.
- PATCH /screenings/{result_id}/expert-assignment: scoped assignments.manage, screening revision, active expert plus school membership and actor-specific eligibility. Reassignment advances both revisions and preserves existing reviewer authorship/status. Existing Vue admin assignment controls still need hosted integration; this slice implements the server boundary.
- GET /screenings/{result_id}/image: current-scope API proxy with no-store/nosniff, private bucket validation and bounded binary download. React never constructs a public image URL or puts a token in an image source.

The database reserves a request before Storage/inference, binds its normalized image digest/student/requested model with the existing private HMAC key, and pins the approved model identity. A processing-key retry never repeats Storage or inference. Completion rechecks access/model/bucket, locks the authoritative student, assigns Initial/Follow-up from completed reports and commits sample, prediction, Pending review, report, request completion and audit together. The unique Initial index remains a second invariant. Inference runs outside the student lock. PostgreSQL row-lock behavior is implemented and sequential competing-reservation tests pass; live multi-connection concurrency and host latency remain unverified.

The server does not delete an object after an uncertain completion. Its failure capability first checks durable completion and queues only uncompleted objects. Failed requests cannot finalize later. A 20-minute abandoned processing request can be expired by reconciliation; the same advisory lock prevents races with completion. Slow workers then cannot create an official result for that expired request.

## Private Storage setup (server only)

Verified 2026-10-20: `tools/check_v1_storage_io.py --apply` passed generated PNG upload, byte-exact authorized download, anonymous public-route denial and deletion with confirmed404. No application DB writes or student images; cleanup receipt removed. This tests only the generated object/current access, not every production policy. User-run catalogue check also passed all12 checks for3 installed published versions and MobileNetV2 default. No setup repetition needed. The following older read-only checkpoint is historical.

2026-10-20 checkpoint: user saved the settings; real S3 HeadBucket and bounded prefix listing passed without writes or private output. Bucket privacy and object put/get/delete remain unverified. Do not repeat credential setup. Restart the API after remaining model configuration, since its current process predates these settings.

Create a **private** bucket in this project's Storage UI, without public client object policies. Generate server S3 credentials and copy endpoint/region from the same project's S3 settings. S3 keys bypass Storage RLS across buckets, so keep them only in the ignored server .env; the adapter itself restricts operations to the configured bucket and generated UUID paths. No Auth-admin/service-role API key is introduced. See [Supabase S3 authentication](https://supabase.com/docs/guides/storage/s3/authentication) and [private bucket behavior](https://supabase.com/docs/guides/storage/buckets/fundamentals).

From the repository root, run:

    .\.venv\Scripts\python.exe .\graphiscan\tools\configure_v1_storage.py

The local CLI hides both credential inputs, validates same-project HTTPS endpoint and saves configuration without printing keys. It does not create a bucket, test connectivity or change database data. Never paste credentials in chat or add them to EXPO_PUBLIC_/VITE_ settings. boto3 is pinned in requirements-v1.txt. S3 provider calls have bounded timeouts and no SDK retry loop; provider compatibility/authenticated live I/O remain to be checked.

## Pin the existing predictor, without inventing evaluation results

Current prepared path: see MODEL_EVIDENCE.md. The owner-supplied evaluation was rerun through hosted preprocessing; `tools/prepare_v1_model_catalogue.py` has staged three hash-pinned artifacts and saved a schema-v2 local manifest. Apply only the prepared `db/postgres/publish_binary_models.sql` data publication next, then restart the API. It selects MobileNetV2 using measured0.75 results and does not change the legacy ResNet50 file. The single-model command below is retained for old installations, not the next setup step here. Do not overwrite the new manifest with it.

Only the existing binary predictor is supported by this runtime adapter: RGB 224x224 input, current class mapping and 0.75 High Potential decision rule. It reuses predict.py functions and does not call its verbose debug wrapper. It preserves fraction scores and reported-class confidence, including Normal when the High Potential score is 0.60. It does not claim evaluated three-class support or synthesize expert recommendations.

The reviewed registry entry must already have matching verified key/version, preprocessing identity, decision rule and actual evaluation evidence before publication. A default must be among the highest evaluated accuracies on its same task/evaluation; ties still require explicit deployment choice. Preparing a manifest does not publish or verify a model. The owner supplied training_results; see MODEL_EVIDENCE.md for the verified artifact match and historical 0.50 versus deployed 0.75 cutoff mismatch. Do not transfer historical accuracy to the hosted pipeline without reevaluation.

After confirming the real registry key/version, run from repository root:

    .\.venv\Scripts\python.exe .\graphiscan\tools\prepare_v1_model_manifest.py --model-key YOUR_REVIEWED_KEY --model-version YOUR_REVIEWED_VERSION

This hashes the existing trusted artifact, class-name file and runtime source, creates ignored model/deployment.local.json without overwriting an existing pin, and saves its server-only path. Artifact/hash/preprocessing mismatches disable the runtime. Deploy artifacts immutably and restart after changing them; no hot swapping or client weight paths are supported. Registry publication/evaluation metadata must be reviewed separately. Server startup remains usable for other routes when Storage/model configuration is absent; uploads then return an unavailable response.

## Reconciliation and client recovery

Schedule the following bounded worker on the server after private Storage is verified:

    .\.venv\Scripts\python.exe .\graphiscan\tools\cleanup_v1_screenings.py --apply

Without --apply it does nothing. It reconciles abandoned requests and deletes only due failed-upload objects not referenced by an official sample. Completed objects are excluded. Failed provider deletion records a safe error code, increments attempts and backs off one hour. Output contains counts only. These are failed/staged objects, not a retention/deletion policy for official records. Do not retire this worker during deployment.

React hosted mode now connects teacher capture/gallery upload and status lookup, exact-key expert-review retries, and protected image viewing/sharing. Pending actions remain in memory: keep the app open until confirmed; app restart does not restore its local key/form/notes. Server recovery is durable, but durable mobile recovery remains future work. No automatic write replay occurs after a network failure. Check request status/current review before explicitly starting another action. Existing legacy mode remains separate and never receives hosted credentials.

Current evidence is isolated PostgreSQL authorization/transaction checks, fictional HTTP/image tests, shared-client retry tests, TypeScript and exports. No real Storage/model upload, eligible-expert hosted write, native camera/share test, APK or production deployment is claimed.
