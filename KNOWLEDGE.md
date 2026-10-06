# GRAPHISCAN system knowledge

## Where to look

- This file: current behavior, local setup, and model details.
- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md): intended workflow, stack, and hosting.
- [PROJECT_PLAN.md](PROJECT_PLAN.md): implementation work order and panel actions.
- [graphiscan/db/MIGRATION_NOTES.md](graphiscan/db/MIGRATION_NOTES.md): database migration mapping.
- The two app READMEs: commands and API origin for each Vue app.

## What it does

GRAPHISCAN screens handwriting images for possible dysgraphia related difficulty. A teacher manages students and uploads samples. A TensorFlow model returns a `normal` or `high_potential` probability, and the application stores a screening result. An expert can review the result and mark its validation `Validated` or `Flagged`; parents can see results for linked students. The output is a screening aid, not a clinical diagnosis.

## Parts of the system

| Part | Location | Purpose |
| --- | --- | --- |
| Flask server | `graphiscan/app.py` | Serves JSON APIs and older server rendered pages; handles accounts, students, uploads, results, validation, progress, reports, and audit logs. |
| Prediction code | `graphiscan/predict.py` | Loads the model on first use, resizes an image to 224 × 224, runs inference, and turns the score into a result. |
| Active model | `graphiscan/model/` | Model, class names, and model metadata used by `predict.py`. |
| User app | `graphiscan/user-app/` | Vue 3 and Vite app for teacher, parent, expert, and guest roles; also has Capacitor Android configuration. |
| Admin app | `graphiscan/admin-web/` | Vue 3 and Vite app for account approval, user and student management, results, progress, settings, and audit logs. |
| Binary training tools | `graphiscan/train_binary_models.py`, `graphiscan/split_binary_dataset.py` | Reproduce the model used by the live app. |
| Three-class training tools | `scripts/split_dataset.py`, `scripts/train_compare_models.py` | Prepare the image-level split and compare experimental Normal / Low Potential / High Potential models. |
| Older interface | `graphiscan/templates/`, `graphiscan/static/` | Flask rendered pages and assets still routed from `app.py`. |

The top level `model/`, `raw_dataset/`, and `scripts/` contain experimental artifacts and training scripts. The running predictor explicitly reads `graphiscan/model/graphiscan_model.keras`, so do not assume a top level model is active.

The active and experimental model paths are explained in [Model details and experiment](#model-details-and-experiment). The three-class data has no writer IDs. `scripts/split_dataset.py` makes a reproducible image-level split without overwriting an existing split, and `scripts/train_compare_models.py` selects by test accuracy. The running predictor is still binary; no new three-class accuracy has been established.

## Main flow

1. Public registration endpoints now refuse account creation; the mobile register route redirects to login. Admin-created accounts remain available. Forced first-login password change and privacy agreement acceptance are still pending.
2. A teacher creates a student linked to a teacher and optionally a parent, then uploads a JPG or PNG handwriting image.
3. Flask saves the image in `graphiscan/static/uploads/`, calls `predict_handwriting`, and writes to `handwriting_samples`, `results`, `validations` (`Pending`), and `reports`. The first report for a student is `Initial Screening`; later reports are `Follow-up Screening` in both upload paths. This uses a count of existing reports and has not been checked against a running database.
4. The model reports `High Potential` when the high potential score is at least 0.75; otherwise it reports `Normal`. The score is stored as a percentage. `graphiscan/model/model_config.json` records the same threshold, but the runtime currently uses the value hard-coded in `predict.py`. The predictor no longer generates AI recommendations. New result rows use an empty value in the legacy `results.recommendation` column until the database migration removes it; result APIs and screens do not expose that column.
5. An expert reviews a result and records validation status, remarks, and follow up information. Teachers and linked parents can see results and student progress. A guest demo runs inference without creating official result records.

On 2026-10-06, parent access in the current MySQL-backed Flask app was narrowed to results whose expert validation status is exactly `Validated`. The parent JSON list, detail, progress, and image-download routes filter on both the linked parent and validation status. The older Flask parent list and shared result/report pages apply the same release rule to parent sessions. Pending and Flagged results remain available to authorized teacher, expert, and admin paths. The Vue parent list now presents reviewed results only. This is source behavior; a synthetic-record Flask test-client check covered owned Validated, Pending, Flagged, and another parent's records without a live database. Uploaded images are still stored under Flask's local static directory, so this route change alone does not make storage private.

## Interfaces and storage

- User APIs: `/api/user/*`; admin APIs: `/api/admin/*`.
- The user and admin Vue apps attach bearer tokens from browser local storage. Flask keeps those tokens in process memory, so restarting the server ends API sessions.
- Flask also has session based routes for the older rendered interface.
- MySQL is configured in `graphiscan/config.py`. The application references `users`, `students`, `handwriting_samples`, `results`, `validations`, `reports`, `audit_logs`, and `password_reset_tokens`. A sanitized schema-only snapshot of a 2026-07-28 local export is now in `graphiscan/db/legacy_mysql_schema.sql`; it may be stale. The original export containing rows remains outside Git. `graphiscan/db/postgres/001_identity.sql` and `002_screening.sql` draft the target tables but have not been applied. `graphiscan/db/MIGRATION_NOTES.md` maps the old tables and lists the remaining migration work.
- Both Vue apps read the public `VITE_API_ORIGIN` build variable, with `http://localhost:5000` as a local fallback. On a physical phone, set the origin to a reachable host. The Vite development ports are 5174 and 5173 respectively.
- The current Vue branding uses the GraphiScan wordmark without standalone letter-G marks. The admin layout no longer shows the top-right account pill; the mobile header and profile use a neutral profile icon instead of a letter avatar. This is a UI source change, not an authentication change.
- The admin and current Vue mobile result/progress views now use screening/model-score language and dated assessment history. The admin dashboard has a compact header and removes duplicate role-distribution and student-monitoring sections; its four summary cards now match the 108px metric card sizing and type scale used by the other admin pages. The Users, Students, Results, Progress, and Audit Logs tables omit row numbers and low-value list columns so actions fit at desktop width. Settings now focuses on its password form instead of a repeated security reminder. Admin and current Vue user routes restore scroll position on browser back/forward and start new pages at the top without an entrance animation. Both apps use Inter from their global stylesheet. The teacher, parent, and expert mobile result lists show one predicted-class model score and the screening date instead of separate Probability and Confidence percentages. Automatic “improving” labels and cross-record score charts have been removed from those views and the Flask progress responses. New predictions use an empty `analysis_summary` because the old canned prose was redundant and could imply clinical interpretation; the required legacy database column remains until migration. Older stored summaries are no longer shown in the current Vue result views or main Flask result/report pages.

The admin source now uses a navigation drawer below 1100px and labeled record cards below 900px for Users, Students, Results, Progress, and Audit Logs. On 2026-09-30, the admin production build passed and those main routes were checked in Chromium at 390px, 768px, and 1365px with mocked API responses and synthetic records; the pages had no document-level horizontal overflow. The drawer opened and closed through navigation in that browser check. This was not a real authenticated backend session or a physical-device test.

The admin desktop layout now uses the page's own heading without a second top-bar title. Its content width can grow to 1600px, reducing unused side space on laptops and wide monitors. Chromium dashboard checks at 390px, 1440px, and 1920px with synthetic records showed one main heading, the compact header only at phone width, and no document-level horizontal overflow. Other detail pages were not visually checked in that pass.

On 2026-10-01, a repeated 16,350-line block was removed from the user app stylesheet after line-by-line comparison confirmed it was identical to the earlier block. Styles dedicated to the deleted registration view and stale registration prompts were removed or updated in the Vue and older Flask pages. The older Flask login page also dropped an unwired Remember me checkbox and a placeholder forgot-password link. The user and admin Vue production builds passed after this cleanup; the changed pages were not visually checked in this pass.

The Settings password form now fills the available admin content width, with the live password requirements beside the fields on desktop and below them on narrow screens. Summary cards share the same 16px corner radius across the dashboard and record pages. On 2026-09-30, Chromium checks at 1440px and 390px showed no document-level horizontal overflow on Settings, Dashboard, Users, Students, Results, Progress, or Audit Logs. The record-page checks used empty mocked API responses and temporary browser-only authentication state; they did not verify a real login or populated records.

## Running it locally

From `graphiscan/`, install Python packages from `requirements.txt`, provide a working MySQL database matching the queries in `app.py`, copy `config.example.py` to the Git ignored `config.py`, and fill a local `.env` using `.env.example`. Then run `python app.py`; the development server listens on port 5000. Each Vue app can be started from its own directory with `npm install` and `npm run dev`. Set the user app API origin for the host or device being used. `graphiscan/model/graphiscan_model.keras` is required for screening but is excluded from Git; provision it separately.

Dependency setup was verified locally on 2026-09-29 with Python 3.11.9 in the root `.venv`. The pinned `graphiscan/requirements.txt` installed successfully; `pip check` found no broken requirements. Flask, Flask-Cors, MySQL Connector, NumPy, Pillow, and TensorFlow 2.21.0 imported successfully, and `graphiscan/app.py` imported with 65 registered routes. The existing model loaded and reported output shape `(None, 1)`. Local MariaDB was reachable and the configured database contained the eight expected tables. The local HTTP server returned 200 for `/api/user/health` and 401 for an unauthenticated admin route. Both Vue projects' installed packages passed `npm.cmd ls --depth=0`; use `npm.cmd` in PowerShell on this machine because its execution policy blocks `npm.ps1`.

On 2026-10-01, Windows Installer repair restored the missing base Python 3.11.9 executable used by the root `.venv`. The virtual environment then passed `pip check`, and Flask loaded its route listing. Flask test-client requests returned 200 for `/api/user/health` and 401 for an unauthenticated `/api/admin/dashboard` request. These checks ran outside the task sandbox because the sandbox blocks access to the interpreter under the user's AppData directory; they did not exercise a live HTTP server or the database.

On 2026-10-06, the base Python 3.11.9 executable was missing again and was restored with Windows Installer repair. Outside the task sandbox, the existing `.venv` reported Python 3.11.9, `pip check` found no broken requirements, `app.py` and `predict.py` compiled, Flask loaded 65 routes, and test-client health/admin checks returned 200/401. The new synthetic parent-access regression tests passed. The user Vue production build passed after the parent view change. No live MySQL or physical-device flow was exercised in this check.

## Current concerns visible in source

- The local `graphiscan/config.py` contains credentials and is excluded from Git. Admin setup scripts now require credentials from `.env`. The Flask entry point still enables debug mode; disable it before any shared deployment.
- The `@app.after_request` handler echoes any request `Origin`, which broadens CORS beyond the list configured through Flask CORS.
- The Capacitor navigation address is still tied to the older local setup; React Native/Expo migration is planned.
- Both Vue READMEs describe local startup. Draft PostgreSQL schema files exist, but have not been applied.

See [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) for the target workflow and hosting plan, and [PROJECT_PLAN.md](PROJECT_PLAN.md) for panel requirements and work status. These migration targets are not live behavior.

The ordered work and current UI status are in [PROJECT_PLAN.md](PROJECT_PLAN.md). On 2026-09-29, both Vue production builds completed successfully. Local login screens and a synthetic-data teacher results list were captured at 390px with an actual Chrome viewport; neither had horizontal overflow. The admin dashboard was visually inspected with synthetic data at desktop width. Read-only Flask test-client requests with existing active role IDs returned 200 for admin dashboard/users/students/progress/results/audit logs, teacher students/results, parent results, and expert results. Only response field names and list sizes were printed. These test-client sessions were temporary and did not authenticate through login. No real authenticated browser session or physical phone was checked. A duplicate font `@import` in the mobile stylesheet was removed after its Vite warning; current client connection errors now use user-facing wording instead of naming Flask. Both client router guards use return-based redirects after Chrome logged a deprecation warning for `next()`.

## Model details and experiment

### What the app runs now

`graphiscan/predict.py` loads `graphiscan/model/graphiscan_model.keras`. This is the **binary** Normal / High Potential model. Its `dysgraphia_probability` field is the model's High Potential score multiplied by 100. The runtime labels a sample High Potential at 75%; `graphiscan/model/model_config.json` records that same value but is not read by the runtime. The reported 86.03% test accuracy is from 136 binary test images, not a per-image probability. The 75% cutoff has not been validated in the project records reviewed so far.

### Three-class experiment

`raw_dataset/` contains 462 Normal, 417 Low Potential, and 435 High Potential JPGs. The images have sequential filenames and no participant IDs, so writer separation cannot be verified. `model/` contains **earlier experimental** three-class models and reports; ResNet50V2 recorded 72% accuracy on 200 images. Those files are not loaded by the app. Do not compare 72% and 86.03% as if they measure the same task.

For a new run, use only these two scripts from the repository root:

1. `py scripts/split_dataset.py` creates `dataset_image_split/` with a reproducible 70/15/15 split. It preserves original filenames and refuses to overwrite an existing split.
2. `py scripts/train_compare_models.py` trains MobileNetV2, EfficientNetB0, and ResNet50V2 on that same split, evaluates all three on the test portion, and selects the highest test accuracy. It writes private artifacts and per-class reports under `model/`.

The split is **by image**, not by child. Report this limitation and do not describe test accuracy as performance on unseen children. The source images, split, model files, and student uploads remain outside Git. Neither script has been run as part of this cleanup.

### Before changing the live app

Review the three-class confusion matrices and per-class precision/recall, especially Normal versus Low Potential. The model score has not been checked for probability calibration; do not present it as a clinical likelihood. Then update inference, storage, teacher model selection, mobile result wording, and expert validation together. Preserve old binary results as binary records. No live three-class deployment has happened yet.
