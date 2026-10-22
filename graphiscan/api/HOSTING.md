# Hosted deployment preparation

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
