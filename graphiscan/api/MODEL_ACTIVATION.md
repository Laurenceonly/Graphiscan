# Model-host activation checkpoint, 2026-10-24

Source PR#9 is merged as `4d2e3b13bec932e722a12b128541a4c1f8fe4465`.
Private artifacts and a fresh release-worktree fetch are verified. The isolated
release completed60 tests (one Windows skip covered by all12 Linux transport
tests),24 PostgreSQL cutover checks and the512MiB serving probe. The original
Keras/source pins and current UI work are preserved.

The user reported successful execution of `publish_lite_binary_models.sql` in
Supabase SQL Editor. This is user-confirmed; the authenticated hosted catalogue
and inference have not yet been checked. No numbered migration was rerun.

## Render sequence

Current checkpoint: user supplied the misspelled key
GRAPHISCAN_MODEL_V1_MANIFEST, was instructed to rename it to
GRAPHISCAN_V1_MODEL_MANIFEST, then reported success after correction. The latest
02:28:16UTC deployment log confirms private-model-bundle-ready/models3,
TensorFlowfalse, one-worker/one-thread sync startup, health200 and Live. This
follows the REQUIRE_MODELtrue instruction; actual environment values were not
read independently. Public probes after correction returned health200 (1.03s),
anonymous me401 and models401. Next test an authenticated fictional teacher
screening, then expert review, parent visibility and Follow-up. No inference,
authenticated catalogue or full role workflow success is yet established by
independent probes. Subsequent user confirmation: app is open in the emulator
and model options are visible. Android bundle/Metro/foreground Expo activity
were checked locally. Next is the first fictional teacher screening submission;
no actual inference has been observed yet.

Earlier checkpoint: supplied deployment log at02:09:11UTC confirms the saved
command uses --workers1 and --thread1, Gunicorn boots a sync worker, and health
checks return200 with Live status. The singular --thread was accepted in this
run; the documented full option remains --threads. Prior build log confirms
private-model-bundle-ready/models3/tensorflow_importedfalse. Both build/start
gates are now met. Next configure the model manifest and REQUIRE_MODELtrue in
one saved environment edit, then verify activation and authenticated inference.
No actual inference or role workflow is established by these logs.

Prior supplied build log: the LiteRT build command is now applied and installs
ai-edge-litert2.3.0 plus NumPy2.4.4. Private fetch still fails with ValueError;
the script intentionally suppresses exception values, so the exact cause is
unresolved. First check the exact GRAPHISCAN_MODEL_ARTIFACT_BUCKET environment
entry, then validated S3 configuration if needed. Keep the manifest absent and
REQUIRE_MODELfalse until private-model-bundle-ready is observed.

Earlier failure: the09:31:40GMT+8 manual deployment of4d2e3b1 failed.
Its supplied log installs only requirements-admin.txt and runs the old start
command, then fails required-model startup validation. The earlier09:14 Live
report did not prove that the model build command had been applied. A fresh
public probe after the failure returned health200 (1.22s), me401 and models401;
this proves the serving API is reachable, not that inference is available.

Recovery sequence used: set REQUIRE_MODELfalse and clear MODEL_MANIFEST together,
then correct and save the actual service build/start commands below. The root
render.yaml still defines admin-only commands; whether this service is managed
by that Blueprint is unverified. Do not enable the manifest until a build log
shows the LiteRT dependencies and private-model-bundle-ready (models3).

Use the existing `graphiscan-admin-api` Free service, branch `main`, root directory
`graphiscan`. Browser automation currently has no connected provider, so these
settings are being applied by the user in the normal dashboard.

1. Environment: add/update `GRAPHISCAN_MODEL_ARTIFACT_BUCKET` to
   `graphiscan-model-artifacts` and `PYTHON_VERSION` to `3.11.9`.
   Keep `GRAPHISCAN_REQUIRE_MODEL=false` and the model-manifest setting absent
   until the build/start commands below are ready. Save.
2. Settings / Build & Deploy: set Build Command to
   `sh tools/build_lite_host.sh`.
3. Set Start Command to
   `gunicorn --config gunicorn.conf.py --workers 1 --threads 1 'hosted_api:create_app()'`.
   Save and confirm the latest build succeeds. Its log must show installation
   of ai-edge-litert and numpy, followed by private-model-bundle-ready with
   models3 and tensorflow_importedfalse. Live status alone is insufficient.
   This privately fetches and checks the model files while retaining the
   admin-only startup configuration.
4. Environment: set `GRAPHISCAN_V1_MODEL_MANIFEST` to
   `model/deployment.litert.local.json` and change `GRAPHISCAN_REQUIRE_MODEL` to
   `true` in the same saved edit. Deploy the latest main revision.
5. Verify Live status, health200, anonymous protected routes401, then the fixed
   fictional teacher/expert/parent upload/review/release/Follow-up workflow.

Existing Auth/database/S3/CORS/cursor values remain server configuration and
must not be copied into chat or committed. One worker/thread is necessary for
the small-host image-decoding memory envelope. The process-RSS benchmark is not
a production throughput claim; authenticated hosted behavior still needs evidence.

## If activation fails

Set `GRAPHISCAN_REQUIRE_MODEL=false` and clear
`GRAPHISCAN_V1_MODEL_MANIFEST` together. The require flag alone controls startup
validation; clearing the manifest is what removes the configured inference
runtime. Restore the previous admin-only build/start commands before a source
rollback. Apply the reviewed `rollback_lite_binary_models.sql` if rolling back
the catalogue. It retains historical model/evaluation rows and report links.

No hosted inference, real role workflow, APK or full-project completion is
claimed at this checkpoint. Overall estimate remains60-65%.
