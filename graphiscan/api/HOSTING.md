# Hosted deployment preparation

## Verified candidate and private provisioning, 2026-10-24

The existing Render Free API is the selected pilot target. Deployment/cutover is
still pending; public inference remains disabled. No paid plan or new compute
service was created. The older investigation below records earlier states.

The exact FP32 copies passed a separate Linux TensorFlow comparison on all136
test images/all3 architectures: zero class disagreements and max score error
8.41e-6. `api/litert-linux-evaluation.json` contains aggregate evidence only,
SHA-256 `e9eb1beae81bb85ef0a24dd3349e646fd02ab0598017cbbcf84e8a3a1a324db1`.
ResNet50 uses verified builtin CPU kernels; the others use the CPU delegate.
Schema3 kind `litert-fp32-builtin-resnet-v1` and adapter byte pins bind that choice.
Original Keras weights, manifest, preprocessing/.75 rule and local .env are intact.

The rebuilt serving image passed an actual Linux512MiB cgroup cap with one CPU,
no swap/network and a generated16MP/6.7MB detailed PNG:422.59MiB peak process RSS,
zero OOM kills, external calls or TensorFlow imports. The whole-container peak
reached the cap including charged page cache. This is sequential local evidence;
actual hosted Auth/Storage/Gunicorn overhead and throughput still need checking.
48 model/backend/write tests,12 Linux transport tests and24 isolated PostgreSQL
cutover/rollback checks pass. A separate reference image used3GiB for TensorFlow;
that image is not the serving configuration.

Private `graphiscan-model-artifacts` in the existing Supabase project contains
six verified content-addressed chunks/four files (121266151 bytes). Chunks are
at most32MiB, below the [Free project's50MB object ceiling](https://supabase.com/docs/guides/storage/uploads/file-limits).
The binary bucket is private and separate from student images. No model bytes,
credentials or student images are in the public repository; the committed
`model/litert-bundle.json` is hash/size/path metadata only.

Owner-only local preparation, using the already supplied original artifacts:

```powershell
& .venv/Scripts/python.exe graphiscan/tools/prepare_v1_lite_catalogue.py --comparison graphiscan/api/litert-linux-evaluation.json --artifact-dir .local-tools/lite-model-experiment --refresh-draft
& .venv/Scripts/python.exe graphiscan/tools/prepare_v1_lite_bundle.py
& .venv/Scripts/python.exe graphiscan/tools/upload_v1_lite_bundle.py --bucket graphiscan-model-artifacts
& .venv/Scripts/python.exe graphiscan/tools/prepare_v1_lite_publication.py
node graphiscan/tools/check_v1_lite_publication.mjs
```

`--refresh-draft` backs up and updates only the separate unpublished adapter/
runtime-kind pins; changed artifact identities are refused. None of these
preparation tools applies SQL or changes the original manifest/local .env.
The upload command deliberately reads existing server-only configuration and
creates/reuses the private artifact bucket. Other preparation needs no secrets.
New Supabase secret keys use only the `apikey` header, [not bearer JWTs](https://supabase.com/docs/guides/getting-started/api-keys).

For a fresh native Render build from `graphiscan/`, install `requirements-lite.txt`
then run `tools/fetch_v1_lite_bundle.py`. `GRAPHISCAN_MODEL_ARTIFACT_BUCKET` selects
the separate private bucket; existing trusted-project S3 environment variables
remain server-only. Fetch verifies every streamed chunk, file size/SHA and pinned
runtime, installs the manifest last, and fails the build on any mismatch.
Set the model manifest to `model/deployment.litert.local.json`, require the model,
and use one Gunicorn worker/thread. Startup denies missing runtime or Storage.

`publish_lite_binary_models.sql` atomically publishes the three new versions,
retires the exact previous selectable versions and keeps MobileNetV2 default.
`rollback_lite_binary_models.sql` restores the previous flags/default without
deleting any model/evaluation or historical result. Both guard existing metadata
and unexpected defaults; no numbered schema migration is needed. They are
prepared/tested only, not yet applied to hosted PostgreSQL.

Before a source rollback, restore the admin-only build/start configuration and
`GRAPHISCAN_REQUIRE_MODEL=false`, clear the model-manifest setting, and apply the
reviewed catalogue rollback if publication occurred. Preserve all historical
model/evaluation rows. Then deploy the previous API revision and verify health,
sign-in and protected routes. Hosted role workflow remains the release test.

## Earlier Windows investigation, 2026-10-23

Commands and pending gates in this historical section describe that checkpoint;
use the current preparation above for the builtin-ResNet candidate.

User authorized enabling online screening. New `tools/profile_v1_models.py`
profiles the hash-pinned catalogue with generated lines only, never loading
configuration or accessing Auth/database/Storage. Run from the repository root:

```powershell
& .venv/Scripts/python.exe graphiscan/tools/profile_v1_models.py --output .local-tools/model-memory-profile.json
```

Observed on Windows/Python3.11.9: peak resident416.55MiB with MobileNetV2,
485.46MiB after EfficientNetB0,799.12MiB with all3 cached including ResNet50;
final private memory1597.96MiB. Warm synthetic inference was0.405/0.750/0.808s.
These measurements do not establish Linux container fit or networked throughput.
The existing512MB free service is not established as capable of this runtime.

Separate FP32 LiteRT copies passed comparison against all three originals on
the existing136-image split: zero classification disagreements, maximum score
error9.15e-6 and identical confusion matrices. No quantization or retraining ran.
See MODEL_EVIDENCE.md for exact hashes and limitations. Original weights, source
pins, active manifest/environment, registry and public deployment are unchanged.

The optional schema3 `v1_lite_models.py` adapter retains the upload service's
versioned identity contract and the exact binary mapping/preprocessing/.75 rule.
Converted artifacts require distinct versions and digests. One locked cached
model avoids retaining every architecture. `v1_backend.py` dispatches schema3
while schemas1/2 still use the original factory; admin-only setup does not import
LiteRT or TensorFlow.47 model/backend/hosted/write regression tests passed.

Run from the repository root after provisioning the original local evidence:

```powershell
& .venv/Scripts/python.exe graphiscan/tools/experiment_v1_lite_models.py --runtime-dir .local-tools/litert-runtime --compare
& .venv/Scripts/python.exe graphiscan/tools/prepare_v1_lite_catalogue.py
& .venv/Scripts/python.exe graphiscan/tools/profile_v1_lite_models.py --runtime-dir .local-tools/litert-runtime --manifest graphiscan/model/deployment.litert.local.json --output .local-tools/lite-adapter-memory-profile.json
& .venv/Scripts/python.exe graphiscan/tools/profile_v1_lite_host.py --runtime-dir .local-tools/litert-runtime --output .local-tools/lite-host-memory-profile.json
```

Staging validates all3 complete parity results against the original evidence,
source identities and matrices before copying files. It writes only a separate
ignored `model/deployment.litert.local.json` and hash-named `.tflite` files. It
never changes `.env`, original manifests, SQL or registry state. The comparison
needs TensorFlow plus LiteRT; the standalone profiles import no TensorFlow.

Observed Windows resident peaks: all3 LiteRT models retained321.19MiB;
single-cache adapter/model switching253.79MiB; real hosted API composition with
fictional configuration and generated16MP images472.22MiB. The last probe blocks
HTTP/S3/SQL calls and checks health200/unauthenticated models401. It does not
measure authenticated/networked uploads, concurrent requests or Linux limits.
Windows private memory reached567.66MiB. Linux512MB fit is still unverified.

`Dockerfile.lite` uses Python3.11/`requirements-lite.txt`, only the staged LiteRT
copies and one Gunicorn worker/thread, serializing full image decoding as well
as inference. The original Dockerfile and Render blueprint remain unchanged.
Before cutover: validate Linux/package/limit behavior, privately provision model
files, prepare a reviewed new-version registry/default transaction with rollback,
then run authenticated upload/review/release/Follow-up checks. No public model
download, server-secret transfer, paid resource, SQL execution or deployment has
occurred. Docker is absent; WSL2 exists without an installed distribution at the
initial environment check. A separate Linux validation setup is being requested.

Current official terms were rechecked: [Render Free pricing](https://render.com/pricing)
provides512MB; [Hugging Face Spaces](https://huggingface.co/docs/hub/en/spaces-overview)
requires a paid plan for ordinary Docker/Gradio creation; [Modal billing](https://modal.com/docs/guide/billing)
requires a payment method and [spend limits](https://modal.com/docs/guide/budgets)
are separate from usage budgets. Card preference is still unspecified; no model
provider has been selected or provisioned. Older admin-first priorities below
are historical; this dated investigation is current.

Production source update (2026-10-22): PR#1 merged as `2ddb85f`, Render's existing
Free service now follows main, and deployment `dep-dbcmoj3rjlhs73e180n0` succeeded
and reported live. Local `render.yaml` matches main. Older preparation-branch
instructions below are historical; the former branch has not been deleted.

User subsequently confirmed hosted admin login/dashboard works (2026-10-22).
The deployment gate for PR#1 merge is satisfied. Render still tracks
`deploy/free-hosting`; preserve it until the service source is switched after
merge. This confirmation does not establish full account/Storage/model behavior.

Live admin pilot (2026-10-22): `https://graphiscan-admin.vercel.app/login`
uses `https://graphiscan-admin-api.onrender.com`. Render Free/Singapore service
`srv-dbcm8kqvcj2c73f4ou6g` reported Live from `a3be7a5`; Vercel production
deployment `dpl_Dwy8mZ6Gdbxe3orr6JhudtpFL6rY` is READY. Private server settings
and database CA Secret File were uploaded without printing values. Public login,
API liveness and exact-origin login preflight returned200. Authenticated hosted
dashboard/records/Auth/Storage behavior is still awaiting user private sign-in.
Model inference is disabled; no APK or model-host deployment is implied.
Earlier preparation-only checkpoints below are historical.

Current admin release preparation (2026-10-22): user resumed deployment after
admin completion. Vercel CLI login is confirmed and existing GitHub PR#1 targets
the preparation branch. Render remains at login; no service/deployment or server
secret transfer has occurred. See `ADMIN_RELEASE.md` for the current019 rollout
and admin-only release checklist. `render.yaml` now includes a private Auth-key
placeholder required for hosted issuance/reset/delete. Model hosting remains
separate and must stay free.

## Current decision, 2026-10-22

The user requires free model hosting. The previously recorded Cloud Run choice
is on hold while a suitable free service is selected. No deployment or billable
resource has been created for the model. Provider eligibility, account access,
memory and sleep/usage limits must be established before claiming online screening.

Admin: Vue/Vite on Vercel, sourced from GitHub. Data, Auth and private handwriting
images: the existing Supabase project. Android: installed Expo app built through
EAS. The public API origin must be HTTPS in both clients. A localhost origin does
not work for a public deployment.

## Free-host review and immediate focus, 2026-10-22

User reconfirmed that admin is the immediate focus. Finish the real admin/API/
Supabase workflow and Vercel publication before expanding model-host work. A
temporary admin-only API can run with `GRAPHISCAN_REQUIRE_MODEL=false` and no
model manifest; this does not establish online screening. The model host remains
unselected. Recommendations below are research, not deployed/verified behavior.

| Service | Current documented offer | Project assessment |
| --- | --- | --- |
| Render | Free web service,512MB RAM; sleeps after15 idle minutes | First candidate for the lightweight admin API; existing TensorFlow models need memory measurements. |
| Hugging Face | Regular CPU Docker/Gradio Space creation now requires a paid plan; eligible personal accounts have a free ZeroGPU exception | Do not treat CPU Basic's FREE hardware label as a free account-level deployment. ZeroGPU uses Gradio and targets PyTorch, so it is not a direct replacement for this Flask/TensorFlow app. |
| Modal | Starter includes $30 monthly credits; payment method required; spend limits stop additional out-of-pocket workloads | Candidate for the model-enabled backend if card verification is acceptable and the no-spend setting is confirmed before use. |
| Oracle Cloud | Always Free ARM allocation currently equivalent to2 OCPUs/12GB RAM; card verification and capacity restrictions | More memory, but requires VM administration and ARM/TensorFlow/container checks. |
| Railway | Free plan has $1 monthly credit and0.5GB RAM per service | Small allowance and same memory concern; not the first model-host candidate. |
| Koyeb | One free512MB instance; card verification and paid signup-plan pitfalls | No clear memory advantage over Render for these models. |

Official sources checked2026-10-22:
- https://render.com/docs/free and https://render.com/docs/compute-plans
- https://huggingface.co/docs/hub/spaces-overview and https://huggingface.co/docs/hub/en/spaces-zerogpu
- https://modal.com/pricing , https://modal.com/docs/guide/billing and https://modal.com/docs/guide/budgets
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm and https://www.oracle.com/cloud/free/
- https://docs.railway.com/pricing/plans
- https://www.koyeb.com/docs/reference/instances and https://www.koyeb.com/docs/faqs/pricing

## Backend container

`hosted_api.py` mounts only the v1 API through the existing Supabase composition;
it does not import the old MySQL app. `gunicorn.conf.py` runs one worker and two
threads, avoiding separate model caches in multiple worker processes. The host
supplies HTTPS and `PORT`; Gunicorn listens on all interfaces.

`Dockerfile` uses `requirements-hosted.txt`, Python 3.11 and CPU TensorFlow/Keras.
It copies only the hosted modules, access snapshot SQL and provisioned model
files. `.dockerignore` uses an allowlist, excluding credentials, datasets and
student images. No model binaries are committed to GitHub.

Before building, privately provision `model/deployment.local.json`,
`model/class_names.json`, and the three pinned artifacts under `model/versions`.
The manifest must match the exact deployed runtime source and artifact bytes.
Root `.gitattributes` preserves the exact bytes of the three pinned Python
modules and class mapping across Windows/Linux Git checkouts. Line-ending
normalization would otherwise invalidate the verified manifest.
The container includes these artifacts privately; deployment from a fresh Git
checkout needs a separate private provisioning step. No public model download
or automatic secret transfer is configured.

From `graphiscan/`, a local container build is:

```sh
docker build -t graphiscan-api .
```

The production command is:

```sh
gunicorn --config gunicorn.conf.py 'hosted_api:create_app()'
```

The model runs lazily through the existing hash-pinned runtime. No preprocessing,
threshold, model selection, classification or evaluation behavior is changed by
this packaging. Resource usage and container startup have not yet been measured.

## Private runtime configuration

Use the host's secret/environment settings. Do not commit or put server values
into any `VITE_` or `EXPO_PUBLIC_` variable.

- Existing `GRAPHISCAN_V1_BACKEND`, trusted Supabase URL and publishable key.
- Existing separate reader, password-writer and admin-writer database URLs.
- Existing private Storage bucket and S3 endpoint/region/credentials.
- `GRAPHISCAN_V1_CURSOR_SECRET`: one persistent random 32-byte hex secret shared
  by every replica. Rotate it to invalidate existing pagination cursors. Binding
  to actor/session/filter and the existing 30-minute expiry remain enforced.
- `GRAPHISCAN_CORS_ALLOWED_ORIGINS`: comma-separated exact HTTPS browser origins.
- `GRAPHISCAN_V1_MODEL_MANIFEST`: the container sets this to
  `/app/model/deployment.local.json`.
- `GRAPHISCAN_REQUIRE_MODEL`: defaults to `true`. Missing/invalid models or
  private Storage then prevent startup. Setting `false` is only for an explicitly
  admin-only preparation instance; model uploads remain unavailable.

The existing `/api/v1/health` is liveness only. A 200 response does not establish
database/Auth/inference readiness. Validate scoped sign-in, onboarding, records,
private images and actual screening independently after deployment.

## Frontend and mobile

Vercel project root: `graphiscan/admin-web`; Vite build; output `dist`.
The build needs shared source outside that root. Set `VITE_HOSTED_API_ORIGIN`
to the actual API origin before building. The main hosted login is `/login`.
The old `/legacy-login` and legacy admin pages are not part of the hosted backend.
Automatic Vercel deployment is disabled for the preparation branch
`deploy/free-hosting` until a valid public API origin and runtime are ready.

For Expo, select `EXPO_PUBLIC_API_MODE=hosted` and set
`EXPO_PUBLIC_HOSTED_API_ORIGIN` to that same API origin, then create a new build.
An Expo JavaScript export is not an Android APK or a physical-device check.

## Current verification

Offline hosting/backend tests and a fresh admin build are recorded in the root
change log as they complete. A Docker build, Linux TensorFlow inference, live
deployment and physical Android release checks have not been completed.
