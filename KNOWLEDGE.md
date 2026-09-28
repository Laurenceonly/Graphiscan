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
| Training tools | `graphiscan/train_binary_models.py`, `graphiscan/split_binary_dataset.py` | Prepare binary data and train or compare candidate models. |
| Older interface | `graphiscan/templates/`, `graphiscan/static/` | Flask rendered pages and assets still routed from `app.py`. |

The top level `model/`, `model_old_binary_backup/`, `raw_dataset/`, and `scripts/` contain other artifacts and scripts. The running predictor explicitly reads `graphiscan/model/graphiscan_model.keras`, so do not assume a top level model is active.

## Main flow

1. A guest can register immediately. Teacher, parent, and expert registrations start as `pending` and need admin approval. Public admin registration is disabled.
2. A teacher creates a student linked to a teacher and optionally a parent, then uploads a JPG or PNG handwriting image.
3. Flask saves the image in `graphiscan/static/uploads/`, calls `predict_handwriting`, and writes to `handwriting_samples`, `results`, `validations` (`Pending`), and `reports` (`Initial Screening`).
4. The model reports `High Potential` when the high potential probability is at least 0.75; otherwise it reports `Normal`. The probability is stored as a percentage. `graphiscan/model/model_config.json` says `threshold: 0.5`, but the runtime uses the 0.75 value in `predict.py`.
5. An expert reviews a result and records validation status, remarks, and follow up information. Teachers and linked parents can see results and student progress. A guest demo runs inference without creating official result records.

## Interfaces and storage

- User APIs: `/api/user/*`; admin APIs: `/api/admin/*`.
- The user and admin Vue apps attach bearer tokens from browser local storage. Flask keeps those tokens in process memory, so restarting the server ends API sessions.
- Flask also has session based routes for the older rendered interface.
- MySQL is configured in `graphiscan/config.py`. The application references `users`, `students`, `handwriting_samples`, `results`, `validations`, `reports`, `audit_logs`, and `password_reset_tokens`. No SQL schema or migrations were found in this workspace.
- `graphiscan/user-app/src/api/userApi.js` currently points to `http://192.168.1.43:5000`; `graphiscan/admin-web/src/api/adminApi.js` points to `http://127.0.0.1:5000`. The Vite development ports are 5174 and 5173 respectively.

## Running it locally

From `graphiscan/`, install Python packages from `requirements.txt`, provide a working MySQL database matching the queries in `app.py`, copy `config.example.py` to the Git ignored `config.py`, and fill a local `.env` using `.env.example`. Then run `python app.py`; the development server listens on port 5000. Each Vue app can be started from its own directory with `npm install` and `npm run dev`. Set the user app API origin for the host or device being used. `graphiscan/model/graphiscan_model.keras` is required for screening but is excluded from Git; provision it separately.

These are source based setup notes; the application and database were not run during this review.

## Current concerns visible in source

- The local `graphiscan/config.py` contains credentials and is excluded from Git. Admin setup scripts now require credentials from `.env`. The Flask entry point still enables debug mode; disable it before any shared deployment.
- The `@app.after_request` handler echoes any request `Origin`, which broadens CORS beyond the list configured through Flask CORS.
- The user app API address and Capacitor navigation address are fixed to particular LAN hosts, making device setup dependent on the current network.
- Both Vue READMEs are still the default Vue and Vite template, and there is no database schema or migration file here.
