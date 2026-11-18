# Current manuscript revision guidance

Adopted 16 November 2026 at the user's instruction to follow
`C:/Users/MY_PC/Downloads/GraphiScan_Manuscript_Revision_Log (1).pdf`
(seven pages). Use its section headings and figure/table captions as locators;
its original 73-page basis does not establish current pagination. This is the
current guide for continuing manuscript review, ahead of conflicting older
checklist suggestions. The PDF log records reported edits, not independently
verified insertion into the current manuscript. Do not restart reported revisions
as though no prior work occurred, or mark them verified without checking.

## Decisions to preserve

- Official title: GRAPHISCAN: A Dysgraphia Detection and Management System Using
  Convolutional Neural Networks.
- Retain Agile per the user's November 15 clarification. Use the WBS phases
  Planning, Analysis, Design, Implementation, Testing, Deployment and Maintenance.
- Preserve the original Gantt style; check Deployment in 2027 followed by
  Maintenance. Expert validation is scheduled for 2027; the 2026 pre-defense
  requirement was the validator agreement. Do not add a separate expert-validator
  Gantt activity without a further user decision.
- Keep the Performance Comparison heading `Avg Accuracy (%)`.
- Keep the Validation Table unchanged and retain the seven-entity ERD structure;
  do not redesign without confirmed schema differences.
- Avoid unnecessary paraphrasing, including the retained confusion-matrix explanation.
- Do not count the discarded generated Context Flow Diagram as inserted.
- Exclude References-section corrections. The suggestion to remove literature
  about other learning disabilities remains deferred.

## Content direction

Follow the log's section-by-section revisions for objectives, terminology,
requirements, architecture, diagram explanations, dataset/model methodology,
results, implementation, security and maintenance. Preserve binary Normal/High
Potential screening, the distinction from diagnosis, expert-authored remarks and
recommendations, administrator-issued accounts, and the Vue admin / Expo Android
/ Flask API / Supabase Auth / PostgreSQL / private-storage architecture.
The log retains 897 selected images split 627/134/136 and names MobileNetV2,
EfficientNetB0 and ResNet50. Verify runtime preprocessing and evaluation provenance
before using these statements as current system or model evidence.

## Open verification

- Final insertion and connections of the architecture figure and revised Gantt.
- Supported browsers/devices; archiving; expert MFA; configured backup schedule
  and tested recovery; dataset annotation and collection-condition evidence.
- EfficientNetB0 conflicting Normal-class metrics and the Figure 19 placeholder.
- Role permissions, provisioning/onboarding and model selection/deployment claims.
- Evaluation provenance: the log retains historical ResNet50 117/136 = 86.03%
  and MobileNetV2 High Potential 64.65% precision / 96.97% recall / 77.58% F1.
  These differ from the newer selected-version validation/test evidence recorded
  in this repository. Keep evaluation versions, splits and thresholds separate;
  do not silently overwrite either set or infer the current default from this log.

The November 16 comparison found the two available 75-page manuscript PDFs have
identical whitespace-normalized text, with rendering changes only on pages 12-16.
That comparison remains valid, but does not disprove revisions in a separate
working manuscript referenced by this log. No manuscript was edited when adopting
this guidance.
