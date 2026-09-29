---
name: graphiscan-screening-review
description: Review GraphiScan screening result language or behavior against the active predictor and result flows before changing user-facing claims.
---

# GraphiScan screening review

Use this skill when reviewing or editing screening labels, scores, explanations, or result flows.

1. Read `AGENTS.md` and the relevant sections of `KNOWLEDGE.md`. Check `graphiscan/predict.py` for the runtime classes, preprocessing, and threshold; do not infer active behavior from training scripts or top-level model files.
2. Trace the affected result through the JSON API and older Flask routes in `graphiscan/app.py`, then through the relevant Admin or User Vue view. Check server-side role and ownership rules when records are involved.
3. Distinguish a model score from a clinical probability or diagnosis. Keep the live binary labels distinct from any planned three-class model, and attribute expert notes to the expert.
4. When changing behavior, verify the affected build or runtime path and update `KNOWLEDGE.md` if model behavior, endpoints, architecture, or setup changed. State separately what source inspection showed and what was tested by running the system.
5. Report any mismatch with file paths and the smallest correction. Never include credentials, student images, or database rows in the report.
