# GraphiScan paper-to-system alignment guide

**15 November methodology clarification:** User confirms Agile. Keep the Agile
figure and methodology text; align WBS and Gantt phase names/counts with that
approach. The earlier Hybrid figure replacement task is superseded by this
direction; no separate adviser approval is inferred.

**15 November current-PDF review:** User supplied `GraphiScan (1).pdf`, 75 pages.
Use [DEFENSE_CURRENT_PDF_REVIEW.md](DEFENSE_CURRENT_PDF_REVIEW.md) for current page
references and observed completion. It confirms four italicized RRL themes,
shared use cases and stated nonfunctional requirements, but identifies continuing
methodology/WBS/onboarding/diagram gaps and new selected-model table/figure errors.
The older 76-page review below is historical where it conflicts. PDF not edited.

**13 November update:** The production model registry now sets fine-tuned ResNet50 as the default, based on the highest displayed test accuracy. All three selected models are selectable. The 134-image validation comparison instead ranks MobileNetV2 first. Neither ranking proves generalization; authenticated hosted inference for each model remains to be checked. Use the proposed replacement text below to align the manuscript with the app.

Initially reviewed 10 November 2026 against `C:/Users/MY_PC/Downloads/GraphiScan.pdf` (76 PDF pages); model-selection guidance updated 12 November using the selected validation package and current recorded project evidence. **Page references below are PDF viewer pages**, not necessarily printed page numbers. This is a revision guide, not a revised manuscript or proof of clinical effectiveness. Text extraction was reviewed; embedded diagrams and graph details require visual inspection in the editable paper.

## What the paper should consistently describe

GraphiScan is a **handwriting-image screening and record-management system**, intended to support, not replace, professional assessment. An authorized teacher submits a student's handwriting image; a CNN produces one of two labels, **Normal** or **High Potential**. An authorized expert can review the result and provide human-written remarks, recommendations and follow-up decisions. Authorized users see records according to their role and relationship to the student. An initial screening may be followed by later screenings; an expert may also finalize a whole-history conclusion when the applicable conditions are met.

The active hosted design uses the Expo Android app for teacher, expert and parent workflows; a Vue admin web application; a Flask API; Supabase authentication, PostgreSQL and private image storage; and server-side model inference. Older Flask/MySQL and user-web code also exists; don't present all old and hosted paths as a single current deployment. Source implementation, local tests, deployment and real-user acceptance are distinct levels of evidence.

## Priority revisions by PDF location

| Location | Paper issue | Revision needed and basis |
| --- | --- | --- |
| Cover and throughout, pp. 1–9, 20–21, 46–66 | Titles and body alternate between “detection,” “diagnose,” and “screening”; pp. 6–7 claim diagnosis, definitive recommendations and guaranteed identification/intervention. | Agree on one approved title; if the institution permits, use “screening” instead of diagnosis in the title. Across objectives, significance, definitions, results and conclusion, say **screening for possible indicators**, not diagnosis, guaranteed detection or treatment. A Normal label does not rule out a difficulty. An expert review is not itself evidence of clinical diagnosis. |
| pp. 3–5, 11, 13–19 | Claims AI is unquestionably effective, unbiased, objectively measures specific features, that no automated systems exist, and that GraphiScan meets all comparison criteria including handwriting recognition and intervention. | Qualify literature claims and check each cited source. The classifier learns image patterns; the implemented output does not individually measure or explain spacing, stroke or motor control, transcribe text, or provide real-time intervention. Revise Table 1 to compare only supported capabilities and cite evidence for each claim about other systems. |
| p. 5 and throughout | A percentage is described as the probability that a child has dysgraphia. | Describe it as the **model's High Potential score for an image**, not a clinically calibrated probability or model accuracy. At the current rule a score of at least 0.75 gives High Potential; below 0.75 gives Normal. Explain this is an operational decision threshold, not a 75% chance of diagnosis. See `graphiscan/predict.py`. |
| p. 6 | Objective names ResNet50V2, implies diagnosis, and says one best model is deployed using accuracy, precision, recall, F1 and computational efficiency. | Correct architecture name to **ResNet50**. State the three model families and their binary classification purpose, human review and role-controlled record management. The production catalogue makes fine-tuned ResNet50 the default and allows manual choice. No overall ranking based jointly on all listed criteria has been established. |
| pp. 8–9 | Scope includes age/grade applicability, automated tailored feedback, progress improvement, and a confusing offline sentence. | Keep Grades 1–3 as the intended application scope, distinguish that from ages and provenance of the training dataset, and describe internet dependence. Recommendations are written by the expert; stored history does not automatically establish improvement. Avoid implying the data establish validity for every Grade 1–3 population. |
| pp. 18–21 | Comparison table/definitions promise transcription, automatic intervention and diagnostic output. | Define binary classification, model score, expert review, Validated/Flagged/Pending, Initial/Follow-up and final report consistently with the actual workflow. Remove unsupported feature ticks or label them as future work. |
| pp. 22–28 | Methodology calls Figure 5 Agile SDLC; WBS alternates between PADIM, six phases, and seven including deployment. Architecture states MySQL and guest self-registration. | User confirms Agile on November 15. Retain Agile and make the figure, text, WBS and Gantt use consistent phases; distinguish planned from completed activities. The earlier Hybrid replacement task is superseded. Redraw hosted architecture with Expo, Vue admin, Flask API, Supabase Auth/PostgreSQL/private Storage and server inference. Guests do not self-register: authorized administrators issue accounts; first password change and privacy acceptance gates apply. |
| p. 29 | Outputs list Low Potential, and imply all roles see all reports and an automatic progress assessment. | Remove **Low Potential** from system outputs: the current agreed scope is binary. Show the model score, review status and expert-authored remarks/recommendations; describe role and student scope. Do not claim the system calculates improvement. |
| pp. 30–34 | Requirements claim self-registration, grayscale/noise removal, educational content based on results, automatic description/improvement, simultaneous uploads without degradation, archiving and broad compatibility. | Rewrite as testable requirements matching implemented behavior. Preprocessing uses image normalization and RGB 224×224 resizing in the inspected runtime, not a demonstrated grayscale/noise-removal pipeline. Remove or identify unimplemented features as proposed. The 5-second result/upload and 3-second page targets are **requirements**, not achieved results without measured conditions and evidence. |
| pp. 34–38 | Use-case, context-flow and DFD descriptions overstate administrator powers, parent access and automatic progress; DFD uses D1 for multiple stores. | Redraw and cross-check actor permissions and flows using the matrix below. Assign distinct labels to distinct data stores and ensure context diagram inputs/outputs balance with Level 1 DFD. Use the actual assignment and access model; show private image storage separately from records. Inspect Figures 10–12 visually and update diagrams as well as prose. |
| pp. 38–45 | ERD/data dictionary assert seven simplified physical tables, integer IDs, probability, automatic summary, licenses, generated PDF and report status fields. | Either label them explicitly as a **conceptual** model or rebuild the physical ERD and data dictionary from current PostgreSQL migrations and actual columns/types/keys. Include identity/roles, schools and assignments, student relationships, screening and image references, model/version, expert reviews, audit and final reports where applicable. Do not invent fields or imply automatic PDF export. |
| pp. 46–49 | Dataset provenance, labeling, age range, preprocessing and split independence are asserted without demonstrated verification. Claims the test set was only used at the final stage. | Check original dataset documentation, consent/license and original training code before retaining provenance, age, label, collection and preprocessing claims. The recorded split is 627 training, 134 validation, 136 test images; exact-image hashes did not overlap, but same-writer/transformed-image leakage is not ruled out. The 136 test images were used in previous comparisons, so call this a **previously used test split**, not an untouched independent test. State that training and runtime preprocessing/thresholds differ where applicable. |
| pp. 52–63, Figures 18–22, Table 11 | Historical numbers are used as current operational performance; ResNet50 is called the sole deployed best model. Table 11 says 89.03%, while text says 86.03%; EfficientNet Normal metrics differ between pp. 53 and 58; p. 53 has an incomplete sentence. | Report both the 134-image validation comparison and the previously used 136-image test comparison separately. MobileNetV2 leads validation; ResNet50 leads the displayed test comparison and is the current registry default. Label data reuse and the limits of both comparisons. Rebuild tables, matrices, charts, captions and narrative consistently; explain the app's rounding of ResNet50 test accuracy. Fix contradictory historical numbers and describe metric-specific tradeoffs rather than claiming one universal winner. |
| pp. 63–66 | Implementation/maintenance states React, Node.js, MySQL, expert MFA, AES-256 at rest, bcrypt, universal audit logging, scheduled retraining/backups and clinical use as established facts. | Correct stack. Retain exact security algorithms, MFA, log coverage, backup frequency, retraining and operational responsibilities only with configuration or operational evidence; otherwise list as proposed or remove. Do not promise that expert-validated data are automatically used for retraining. Distinguish an implementation plan from a completed deployment and tested service. |
| References pp. 67–76 | The review relies on citations that have not been checked in this audit. | Verify every cited paper/dataset actually exists, supports the associated statement, and has accurate authors, publication details and working links; use the required citation style. This guide does not validate medical or bibliographic claims. |

## Suggested revised objectives

These are proposed wording for adviser approval, not a statement that all objectives are achieved:

**General objective.** Develop GraphiScan, a role-controlled system that supports preliminary screening of handwriting images for possible indicators associated with dysgraphia and enables expert review and record management.

1. Develop an image submission and preprocessing workflow using MobileNetV2, EfficientNetB0 and ResNet50 to classify handwriting samples as Normal or High Potential.
2. Evaluate MobileNetV2, EfficientNetB0 and ResNet50 using a documented dataset, model versions, preprocessing, decision threshold and class-specific performance metrics.
3. Enable authorized experts to review and validate or flag screening results and provide recommendations justified by their review, with appropriately scoped access for teachers and linked parents.
4. Assess the system's functional and nonfunctional requirements using documented tests and report any limitations and unverified conditions.

## Defense minutes: manuscript action tracker

Cross-checked against `GraphiScan_Defense_Minutes.md`, the transcription of the June 1 defense. Its page numbers refer to the minutes and may differ from PDF viewer pages above. The minutes' “Action/s Taken” statements are reported actions, not proof that the current manuscript contains the revisions. The 16 recommendations below remain subject to checking the editable manuscript and final figures.

| # | Panel or adviser direction | Paper or presentation action |
| --- | --- | --- |
| 1 | Use all three trained models, with the highest-accuracy model as default. | State that the registry defaults to fine-tuned ResNet50 based on the previously used test comparison; MobileNetV2 had higher validation accuracy. Manual selection is supported in source; hosted inference still needs acceptance testing. |
| 2 | Remove AI recommendations unless supported by a basis. | Remove unsupported automated recommendation claims; retain clearly attributed expert-authored recommendations. |
| 3 | Revise objectives to address analysis, justified recommendations and expert validation. | Include expert validation and link human recommendations to the expert's analysis; reconcile final wording with the adviser. |
| 4 | Name models in objectives and state their purpose. | Name MobileNetV2, EfficientNetB0 and ResNet50 and their binary screening purpose. |
| 5 | Improve readability, slide transitions and visibility of classifications. | Review text and slide contrast, typography and transitions; highlight actual Normal and High Potential labels. Low Potential is an example in the minutes, not a current system output. |
| 6 | Strengthen Background of the Study, minutes pp. 2–5. | Clarify the research problem, evidenced gap and significance; verify supporting citations. |
| 7 | Organize related literature into three or four themes, minutes pp. 10–12. | Group the literature under three or four italicized thematic headings and check each source and claim. |
| 8 | Show use cases shared by two or more actors, minutes p. 38. | Draw shared interactions consistent with actual role permissions and label actor associations clearly. |
| 9 | Specify elementary participants grouped by school and grade. | State intended Grades 1–3 scope and organization by school and grade; distinguish intended participants from the model dataset. |
| 10 | Admin/researcher-created accounts, first-login password change and privacy agreement. | Describe account issuance and both onboarding gates; confirm approved privacy wording and avoid implying participant consent is established by account acceptance. |
| 11 | Distinguish Initial from Follow-up screenings. | Explain the first completed screening and subsequent screenings in text, diagrams and reports; do not equate history with measured improvement. |
| 12 | Methodology image; minutes p. 24 originally requested Hybrid. | User confirms Agile on November 15. Retain the Agile figure; align its phases with text, WBS and timeline. Hybrid replacement is superseded. |
| 13 | Align WBS with the presented model and remove unnecessary components, minutes p. 26. | Revise WBS and its phase names to match the approved methodology and actual work. |
| 14 | Revise and reorganize Use Case Diagram, minutes p. 38. | Reconcile actors, shared use cases and access restrictions with the actual application. |
| 15 | Align DFD with CFD, minutes pp. 39 and 41. | Balance actors and flows across diagrams, distinguish stores, and check supporting descriptions. |
| 16 | State nonfunctional requirements, minutes pp. 34–36. | Write testable requirements and distinguish targets from measurements; report test conditions and unmet or unverified requirements. |

## Workflow and diagram checklist

| Actor | Depict these supported responsibilities | Access qualification |
| --- | --- | --- |
| Administrator / authorized researcher | Issue/manage accounts and appropriate school or expert assignments through the admin interface. | Scope and server authorization apply; do not depict universal unrestricted access. Account credentials are handed over through the agreed process; do not claim automatic email delivery without evidence. |
| Teacher | Manage assigned student information; submit a handwriting image and select an available model; view permitted results and screening history. | Authorized student/school scope applies. First completed screening is Initial; later completed screenings are Follow-up. |
| Expert | Review eligible results, record Validated or Flagged status, remarks, recommendation and follow-up decision. | Applicable assignments/school-grade scope apply. Expert-authored recommendations are not generated by the model. |
| Parent | View information for a linked child, subject to release rules. | Individual screening/report access is Validated-only. The newer final-report rule permits a linked parent to read a current finalized whole-history report even if it includes Flagged reviews; end-to-end acceptance remains unverified. Do not describe Flagged individual reports as released. |

The final summary is distinct from individual screening reports. Current source requires a reviewed Initial, all included screenings reviewed, and the latest review to indicate no follow-up needed. Follow-ups are optional. A changed screening/history, review, assignment or student revision can make a final report noncurrent. Source and database metadata evidence exist; verify the exact deployed app/API and authenticated role workflow before claiming the whole feature is operational in production. See `graphiscan/api/FINAL_SCREENING_REPORTS.md` and the latest `CHANGELOG.md`; the former contains older superseded parent-access and deployment notes.

## Model evidence: do not mix comparisons

The user's chosen model-selection comparison is the validation evaluation of the original MobileNetV2 and fine-tuned EfficientNetB0 and ResNet50 versions. Use this comparison as the primary evidence in the paper's Algorithm Selection section. The validation package reports the same 134 images, RGB/Pillow preparation and 0.75 threshold for all three selected versions. Other recorded evaluations below are separate and must not be substituted for these selected validation results.

| Evidence | Images and threshold | MobileNetV2 | EfficientNetB0 | ResNet50 | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| User-selected validation comparison | Same 134-image validation split; 0.75, RGB/Pillow | 88.06% original | 83.58% fine-tuned | 85.82% fine-tuned | Primary model-selection comparison in the paper; MobileNetV2 ranks first by validation accuracy. |
| Selected versions, runtime-style test evaluation | Previously used 136-image test split; 0.75 | 85.29% original | 78.68% fine-tuned | 86.76% fine-tuned (86.77% in app) | Separate previously used test results; selected fine-tuned models are deployed and ResNet50 is the current registry default. The app rounds its stored five-decimal value. |
| Historical training comparison in the paper / `graphiscan/api/MODEL_EVIDENCE.md` | 136 images; 0.50, historical training pipeline | 72.79% | 75.00% | 86.03% | Historical results; not measured hosted-runtime performance. |
| Original models, runtime-style reevaluation | Same previously used 136 images; 0.75 | 85.29% | 72.79% | 72.79% | Original MobileNetV2 leads this particular comparison; not independent clinical validation. |

### Class-wise results for the user-selected validation comparison

| Selected model version | Class | Precision (%) | Recall (%) | F1-score (%) |
| --- | --- | ---: | ---: | ---: |
| MobileNetV2, original | Normal | 84.42 | 94.20 | 89.04 |
| MobileNetV2, original | High Potential | 92.98 | 81.54 | 86.89 |
| EfficientNetB0, fine-tuned | Normal | 77.01 | 97.10 | 85.90 |
| EfficientNetB0, fine-tuned | High Potential | 95.74 | 69.23 | 80.36 |
| ResNet50, fine-tuned | Normal | 82.05 | 92.75 | 87.07 |
| ResNet50, fine-tuned | High Potential | 91.07 | 78.46 | 84.30 |

The validation confusion matrices use actual classes as rows and predicted classes as columns, ordered Normal then High Potential: MobileNetV2 [[65, 4], [12, 53]], EfficientNetB0 [[67, 2], [20, 45]], and ResNet50 [[64, 5], [14, 51]]. MobileNetV2 has the highest validation accuracy and F1-score for both classes in this comparison. EfficientNetB0 has the highest Normal recall and High Potential precision, while MobileNetV2 has the highest High Potential recall.

The fine-tuned versions were selected after observing this validation set, and the validation data were also used to choose fine-tuning weights. Present these results as model-selection validation results, not as an unbiased estimate of generalization or as test results. The separate selected-version test comparison has High Potential recall values of 51/66, 42/66 and 50/66 respectively, with 5, 5 and 2 false positives. That test split was used in earlier comparisons; writer-level separation is unverified. Neither evaluation establishes clinical performance or writer independence. The production registry was checked on 13 November and shows the selected ResNet50 as default.

### Proposed manuscript replacement: evaluation and app default

Three binary handwriting-image classifiers were evaluated using the same 0.75 High Potential decision threshold. On the 134-image validation split, original MobileNetV2 achieved 88.06% accuracy, fine-tuned EfficientNetB0 83.58%, and fine-tuned ResNet50 85.82%. MobileNetV2 had the highest validation accuracy. These validation images were used in model and fine-tuning selection, so these figures are not independent estimates of performance.

The selected versions were also evaluated with runtime-style image preparation on a previously used 136-image test split. MobileNetV2 correctly classified 116 images (85.29%), EfficientNetB0 107 (78.68%), and ResNet50 118 (86.76% using 118/136). The application displays 86.77% for ResNet50 because it rounds the stored accuracy value of 0.86765. ResNet50 produced two false positives compared with five for MobileNetV2; MobileNetV2 detected 51 of 66 High Potential images, compared with 50 of 66 for ResNet50.

The deployed application offers all three selected models and defaults to fine-tuned ResNet50, the highest-accuracy model in the displayed test comparison; an authorized teacher may select another model. This default does not establish that ResNet50 is universally superior. The test images had been used in earlier comparisons, and writer-level separation was not verified. Further evaluation on an independent, writer-separated dataset is needed before generalizing the results. The model output is a screening aid, and expert review remains part of the workflow.

## Evidence still needed before final submission

- Verify an authenticated app model chooser and actual submission with each selected model. The production registry and Render revision were independently checked on 13 November; hosted inference for every model remains unverified.
- Run and document an authorized teacher → expert → linked-parent workflow, including Initial, optional Follow-up, release/denial and final report. Record device, app/API versions, date and results without exposing student data. Current source or fictional tests alone are not proof of the complete hosted workflow.
- Measure response time and usability on named devices, connection and server conditions; report sample sizes, cold/warm behavior and failures. Keep unmet or unmeasured targets separate from results.
- Confirm dataset origin, permission, labeling method, participant characteristics, writer-level separation and representativeness. Avoid inferring consent or clinical diagnosis from labels.
- Confirm privacy notice, data controller/contact, retention, access and deletion procedures, participant permissions, and actual security/backup arrangements with the project owner. Do not invent them in the paper.
- Update screenshots, diagrams, table/figure numbering, captions, cross-references and citations after the text is revised; visually inspect all PDF figures and chart labels.

## Suggested editing order

1. Agree on title, screening terminology, scope, objectives and final model versions.
2. Reconcile model methods and results with one reproducible evidence set; correct every repeated number, table and graph together.
3. Redraw architecture, use cases, CFD/DFD and ERD; then align functional requirements, workflows and screenshots.
4. Align methodology, WBS and timeline with what the team actually did; mark proposed work clearly.
5. Collect missing acceptance, nonfunctional, dataset and privacy evidence; revise conclusions to match its limits.
6. Verify references and proofread the complete manuscript, including the incomplete text and inconsistent labels.

## Repository evidence consulted

- `KNOWLEDGE.md` and latest `CHANGELOG.md`: current status and evidence caveats; older dated entries can be superseded.
- `CURRENT_REQUIREMENTS.md` and `DEFENSE_SOFTWARE_AUDIT.md`: current scope correction and defense commitments; historical three-class passages are superseded.
- `graphiscan/predict.py`: binary decision rule and preprocessing in the legacy predictor; hosted runtime uses its own versioned integration.
- `output/selected-model-validation-2026-11-10/README.md` and `class_metrics.csv`: user-selected validation versions and metrics. `output/selected-model-test-2026-11-10/README.md` records a separate previously used test comparison. `graphiscan/api/MODEL_EVIDENCE.md` records original-model runtime reevaluation and historical results. Keep these evidence sets separate; deployment status must follow the latest changelog.
- `graphiscan/api/FINAL_SCREENING_REPORTS.md` and latest changelog: report conditions, newer parent-access change and verification limits.

No production actions, model evaluations, authenticated workflows or clinical validation were performed for this paper review.
