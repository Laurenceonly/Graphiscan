# Agent guidance for GRAPHISCAN

Read [KNOWLEDGE.md](KNOWLEDGE.md) for the system map before changing code.

- The active Python application is under `graphiscan/`. `graphiscan/app.py` contains both the JSON API and older Flask page routes. Check both paths when changing shared behavior.
- The active inference artifacts are in `graphiscan/model/`; `graphiscan/predict.py` is the runtime source of truth for preprocessing and classification thresholds. Training and top level model artifacts are separate.
- User app routes and requests live in `graphiscan/user-app/src/router/` and `src/api/`; admin equivalents live in `graphiscan/admin-web/src/router/` and `src/api/`.
- Preserve role and ownership checks on server routes. Client route guards alone do not protect records.
- Do not disclose values from `.env`, `config.py`, or credential setup scripts. Avoid committing real credentials, uploaded student images, or database data.
- Keep the root `.gitignore` protections in place. The repository uses `graphiscan/.env.example` and `graphiscan/config.example.py` as safe setup templates; real configuration and the screening model are supplied separately.
- If architecture, endpoints, model behavior, or setup changes, update `KNOWLEDGE.md` with the verified behavior. Distinguish observed source behavior from behavior checked by running the system.
