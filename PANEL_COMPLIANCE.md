# GraphiScan defense action tracker

Source: `C:\Users\MY_PC\Downloads\GRAPHISCAN_DEFENSE_MINUTES.md` (June 1, 2026). Its numbered transcription is the requirements source. The minutes' “Action Taken” column records what was reported at defense; it does not establish that the present code implements it. The context file describes the original manuscript and may conflict with the panel.

Status below is based on source inspection on 2026-09-29. The system was not run against a database as part of this inspection.

| # | Applies to | Manuscript / presentation action | System action and current status |
| --- | --- | --- | --- |
| 1 | System + manuscript | Report the evaluation method and scores for all compared models consistently. | **Open:** Target PostgreSQL model registry and result-to-model relationship are drafted but not applied. Integrate ResNet, EfficientNet, and MobileNet; default to the best on the same held-out three-class evaluation and allow selection. Live code loads only one binary ResNet50 model. |
| 2 | System + manuscript | Remove unsupported AI advice from the manuscript or document an evidence basis. The minutes say it was removed. | **Changed in source, runtime unverified:** The predictor no longer emits canned advice or analysis prose; new result rows write empty values to the legacy required recommendation/summary columns. Current Vue result views and main Flask result/report pages do not show older stored AI prose. Older values remain in the database until migration cleanup. Expert-written notes remain attributed to the expert. Manuscript text still needs review. |
| 3 | System + manuscript | Revise objectives to include expert validation and clarify that any human recommendation follows analysis. Reconcile this with item 2: removing **AI** advice does not remove expert-authored recommendations. | **Partial:** Expert review/flag routes and screens exist. Check access rules and the report flow. |
| 4 | Manuscript | Name the trained models in the objectives and explain why each was trained. | Item 1 covers the related model-selector implementation. |
| 5 | System + presentation | Improve slide text and transitions. | **Partial, source only:** Admin and current Vue mobile result/progress copy was simplified; unsupported score trends and clinical probability labels were removed from those views and progress API responses. Visual layout and presentation still need review. Live inference is binary; do not display Low before a validated three-class model exists. |
| 6 | Manuscript | Strengthen Background of the Study: problem, gap, significance. | No code change implied. |
| 7 | Manuscript | Reorganize literature review into three or four themes with italicized headings. | No code change implied. |
| 8 | Manuscript diagram | Show shared use cases involving two or more actors. | Existing teacher → expert → parent workflow should match the diagram; the comment does not itself request a new feature. |
| 9 | System + manuscript | State elementary participants and grouping by school and grade in Scope and Limitations. The context specifies Grades 1–3. | **Open:** Target PostgreSQL schools and grade constraints are drafted but not applied. Current student records have grade but no school. Add school data and grouping in API/admin/mobile. |
| 10 | System + manuscript | State that the GraphiScan team (administrator or authorized researchers) creates and provides a temporary account for each user. The user changes that temporary password on first login, then reads and accepts the Data Privacy Agreement before accessing features. | **Partial:** Public registration is now refused in source. Target PostgreSQL identity/consent tables are drafted in `graphiscan/db/postgres/001_identity.sql` but not applied. Issuing temporary credentials, forced first-login change, and agreement gates are absent. Approved agreement wording is needed. |
| 11 | System + manuscript | Explain Initial versus Follow-up screening in workflow and reports. | **Source changed, runtime unverified:** Both upload paths now label the first student report Initial and later ones Follow-up. Target PostgreSQL schema allows only one Initial report per student. Serialize concurrent screenings during API migration. |
| 12 | Manuscript | Replace the methodology image with the Integrated Hybrid Project Management Approach model. | No code change implied. |
| 13 | Manuscript | Remove unnecessary WBS components and align it with that methodology model. | No code change implied. |
| 14 | Manuscript diagram | Revise and reorganize the Use Case Diagram. | Compare its actors and actions with the final application. |
| 15 | Manuscript diagrams | Align the DFD with the CFD. | Compare both with the final data flows after API/storage migration. |
| 16 | Manuscript + system evidence | State the non-functional requirements in the paper. | Measure the stated response-time and other requirements on the final deployed system; they cannot be marked achieved from source alone. |

The manuscript source and presentation deck are not in this workspace. The minutes' reported “Action Taken” text has not been treated as proof that the corresponding manuscript files or system features are complete.

## Consistency rules

- GraphiScan is a screening aid, not a diagnosis. Any probability must state which model and class it represents. A confidence score is not a clinical probability.
- Use exactly `Normal`, `Low Potential`, and `High Potential` only after a validated three-class deployment. Until then, the live system is explicitly binary (`Normal` / `High Potential`).
- Do not infer `Low Potential` by renaming a binary `Normal` result or compare the binary 86.03% result directly with a three-class score.
- AI-generated recommendations are no longer produced or displayed in current source. Remove the obsolete database column and any older stored values during migration; expert-authored observations may remain, clearly attributed to the expert.
- The same account, student, screening, result, and expert-validation rules must apply to the admin website, mobile app, and API. The API is the authority.
- The older Flask-rendered routes remain reachable in source, so changes to shared behavior must cover or retire those routes before deployment.
