# GRAPHISCAN system knowledge

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

The active and experimental model paths are explained in [MODEL_GUIDE.md](MODEL_GUIDE.md). The three-class data has no writer IDs. `scripts/split_dataset.py` makes a reproducible image-level split without overwriting an existing split, and `scripts/train_compare_models.py` selects by test accuracy. The running predictor is still binary; no new three-class accuracy has been established.

## Main flow

1. Public registration endpoints now refuse account creation; the mobile register route redirects to login. Admin-created accounts remain available. Forced first-login password change and privacy agreement acceptance are still pending.
2. A teacher creates a student linked to a teacher and optionally a parent, then uploads a JPG or PNG handwriting image.
3. Flask saves the image in `graphiscan/static/uploads/`, calls `predict_handwriting`, and writes to `handwriting_samples`, `results`, `validations` (`Pending`), and `reports`. The first report for a student is `Initial Screening`; later reports are `Follow-up Screening` in both upload paths. This uses a count of existing reports and has not been checked against a running database.
4. The model reports `High Potential` when the high potential score is at least 0.75; otherwise it reports `Normal`. The score is stored as a percentage. `graphiscan/model/model_config.json` records the same threshold, but the runtime currently uses the value hard-coded in `predict.py`. The predictor no longer generates AI recommendations. New result rows use an empty value in the legacy `results.recommendation` column until the database migration removes it; result APIs and screens do not expose that column.
5. An expert reviews a result and records validation status, remarks, and follow up information. Teachers and linked parents can see results and student progress. A guest demo runs inference without creating official result records.

## Interfaces and storage

- User APIs: `/api/user/*`; admin APIs: `/api/admin/*`.
- The user and admin Vue apps attach bearer tokens from browser local storage. Flask keeps those tokens in process memory, so restarting the server ends API sessions.
- Flask also has session based routes for the older rendered interface.
- MySQL is configured in `graphiscan/config.py`. The application references `users`, `students`, `handwriting_samples`, `results`, `validations`, `reports`, `audit_logs`, and `password_reset_tokens`. A sanitized schema-only snapshot of a 2026-07-28 local export is now in `graphiscan/db/legacy_mysql_schema.sql`; it may be stale. The original export containing rows remains outside Git. `graphiscan/db/postgres/001_identity.sql` and `002_screening.sql` draft the target tables but have not been applied. `graphiscan/db/MIGRATION_NOTES.md` maps the old tables and lists the remaining migration work.
- Both Vue apps read the public `VITE_API_ORIGIN` build variable, with `http://localhost:5000` as a local fallback. On a physical phone, set the origin to a reachable host. The Vite development ports are 5174 and 5173 respectively.
- The current Vue branding uses the GraphiScan wordmark without standalone letter-G marks. The admin layout no longer shows the top-right account pill; the mobile header and profile use a neutral profile icon instead of a letter avatar. This is a UI source change, not an authentication change.
- The admin and current Vue mobile result/progress views now use screening/model-score language and dated assessment history. The admin dashboard has a compact header and removes duplicate role-distribution and student-monitoring sections; its four summary cards now match the 108px metric card sizing and type scale used by the other admin pages. The Users, Students, Results, Progress, and Audit Logs tables omit row numbers and low-value list columns so actions fit at desktop width. Settings now focuses on its password form instead of a repeated security reminder. Admin and current Vue user routes restore scroll position on browser back/forward and start new pages at the top without an entrance animation. Both apps use Inter from their global stylesheet. The teacher, parent, and expert mobile result lists show one predicted-class model score and the screening date instead of separate Probability and Confidence percentages. Automatic “improving” labels and cross-record score charts have been removed from those views and the Flask progress responses. New predictions use an empty `analysis_summary` because the old canned prose was redundant and could imply clinical interpretation; the required legacy database column remains until migration. Older stored summaries are no longer shown in the current Vue result views or main Flask result/report pages.

## Running it locally

From `graphiscan/`, install Python packages from `requirements.txt`, provide a working MySQL database matching the queries in `app.py`, copy `config.example.py` to the Git ignored `config.py`, and fill a local `.env` using `.env.example`. Then run `python app.py`; the development server listens on port 5000. Each Vue app can be started from its own directory with `npm install` and `npm run dev`. Set the user app API origin for the host or device being used. `graphiscan/model/graphiscan_model.keras` is required for screening but is excluded from Git; provision it separately.

Dependency setup was verified locally on 2026-09-29 with Python 3.11.9 in the root `.venv`. The pinned `graphiscan/requirements.txt` installed successfully; `pip check` found no broken requirements. Flask, Flask-Cors, MySQL Connector, NumPy, Pillow, and TensorFlow 2.21.0 imported successfully, and `graphiscan/app.py` imported with 65 registered routes. The existing model loaded and reported output shape `(None, 1)`. Local MariaDB was reachable and the configured database contained the eight expected tables. The local HTTP server returned 200 for `/api/user/health` and 401 for an unauthenticated admin route. Both Vue projects' installed packages passed `npm.cmd ls --depth=0`; use `npm.cmd` in PowerShell on this machine because its execution policy blocks `npm.ps1`.

## Current concerns visible in source

- The local `graphiscan/config.py` contains credentials and is excluded from Git. Admin setup scripts now require credentials from `.env`. The Flask entry point still enables debug mode; disable it before any shared deployment.
- The `@app.after_request` handler echoes any request `Origin`, which broadens CORS beyond the list configured through Flask CORS.
- The Capacitor navigation address is still tied to the older local setup; React Native/Expo migration is planned.
- Both Vue READMEs are still the default Vue and Vite template, and there is no database schema or migration file here.

See [STACK_DECISION.md](STACK_DECISION.md) for the target stack and free-tier hosting plan, and [PANEL_COMPLIANCE.md](PANEL_COMPLIANCE.md) for the distinction between panel requirements and verified source behavior. These migration targets are not live behavior.

The ordered work and current UI checkpoint are in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) and [RESUME_CHECKPOINT.md](RESUME_CHECKPOINT.md). On 2026-09-29, both Vue production builds completed successfully. Local login screens and a synthetic-data teacher results list were captured at 390px with an actual Chrome viewport; neither had horizontal overflow. The admin dashboard was visually inspected with synthetic data at desktop width. Read-only Flask test-client requests with existing active role IDs returned 200 for admin dashboard/users/students/progress/results/audit logs, teacher students/results, parent results, and expert results. Only response field names and list sizes were printed. These test-client sessions were temporary and did not authenticate through login. No real authenticated browser session or physical phone was checked. A duplicate font `@import` in the mobile stylesheet was removed after its Vite warning; current client connection errors now use user-facing wording instead of naming Flask. Both client router guards use return-based redirects after Chrome logged a deprecation warning for `next()`.
