# Current manuscript versus defense minutes

Reviewed 15 November 2026. Source: `C:/Users/MY_PC/Downloads/GraphiScan (1).pdf`,
75 PDF pages, supplied by the user as the current manuscript. All page numbers
below are PDF viewer pages. This review supersedes assumptions that the current
paper/diagrams were unavailable, and supersedes conflicting findings based on the
older 76-page PDF. The PDF itself was not edited.

**Verdict: partially addressed. Several requested revisions are visibly present;
the minutes' Actions Taken column cannot yet be treated as fully fulfilled.**
Software implementation and prior deployment evidence are assessed separately in
DEFENSE_SOFTWARE_AUDIT.md. A manuscript statement does not prove a live workflow.

**Methodology clarification, 15 November:** User confirms the project is to use
Agile. Retain the Agile SDLC figure and narrative. The minutes' earlier Hybrid
image instruction is superseded for this assessment by that explicit direction;
no independent adviser approval is inferred. Remaining work is internal alignment
of the WBS, phase descriptions and Gantt chart with the chosen Agile approach.

## All 16 recommendations

Rows follow the order of entries in GraphiScan_Defense_Minutes.md.

| # | Panel direction | Current PDF finding | Status / correction |
| --- | --- | --- | --- |
| 1 | Use all trained models; highest accuracy default; allow other choices | pp. 52-62 compare the three selected versions using validation results, with MobileNetV2 strongest. p. 6 still proposes deploying the highest-performing model. The PDF does not explain all three selectable models or the current ResNet50 production default. | Partial. Describe all three choices and separate the validation selection comparison from the previously used test comparison behind the deployed default. Do not change the reported validation winner to ResNet50. |
| 2 | Remove unsupported AI recommendations or establish their basis | p. 6 names expert validation before recommendations, but pp. 8, 19-21 and 31 still describe system feedback/intervention/educational-content functions without consistently identifying the human author. | Partial. Consistently attribute recommendations to the expert; remove unsupported automatic advice or intervention claims. |
| 3 | Revise objectives toward analysis, justified recommendations and expert validation | p. 6 explicitly includes expert validation in objective 4. The general objective still says diagnose; objective 2 still implies a single deployed winner and uses ResNet50V2. | Partial. Expert validation is present. Revise the remaining objective wording and explicitly connect human recommendations to expert analysis. |
| 4 | Elementary participants organized by school and grade | p. 8 specifies elementary Grades 1-3. It does not clearly state grouping of participants by school and grade. | Partial. Keep Grades 1-3 and explicitly state organization by respective school and grade level. Distinguish target users from dataset provenance. |
| 5 | Admin/researcher issues accounts; first-login password change; privacy agreement before features | pp. 29 and 31 still describe guests signing up and user registration/profile creation. No mandatory first-login password-change/privacy-acceptance workflow was found in the extracted manuscript text. | Not adequately documented. Replace self-registration descriptions with the implemented administrator issuance and server-enforced onboarding sequence. |
| 6 | Distinguish Initial and Follow-up screenings | p. 45 gives Initial Screening and Progress as report examples. No explicit first-completed=Initial, subsequent=Follow-up rule was found. | Not adequately documented. Describe saved Initial/Follow-up types and optional follow-ups, including diagram/report terminology. |
| 7 | Methodology figure (minutes originally request Hybrid; current direction is Agile) | pp. 22-24 describe Agile SDLC and Figure 5 shows Agile SDLC. User explicitly confirms Agile on November 15. | Aligned with current direction. Retain Agile; no Hybrid replacement task. Align WBS and timeline with it. |
| 8 | Name models in objectives and state purpose | p. 6 names MobileNetV2, EfficientNetB0 and ResNet50V2 and describes handwriting classification/performance evaluation. Later sections correctly use ResNet50. | Partial. Names and purpose are present; correct ResNet50V2 to ResNet50 and align deployment wording. |
| 9 | Readable colors/fonts, highlighted classifications, smoother presentation transitions | Manuscript text and inspected figures can be read, though several diagrams have very small labels. The PDF does not establish current app classification emphasis or slide transitions. | App evidence remains separate. Final presentation transitions are unverified; enlarge diagram labels. No three-class requirement follows from the minutes' label examples. |
| 10 | Strengthen Background of the Study | pp. 2-5 discuss the problem, Philippine/local context, practical-system gap and significance. p. 3 still calls AI efficacy unquestionable and asserts no automated detection systems, despite discussing existing systems elsewhere. | Structurally addressed, with substantive corrections remaining. Qualify broad claims and substantiate the specific gap. This review does not verify cited research. |
| 11 | RRL in three or four themes with italic headings | pp. 10-12 visibly show four italicized themes: Dysgraphia and Learning Disabilities; AI and Deep Learning in Handwriting Analysis; Image Processing for Handwriting Recognition; Early Detection and Technology-Assisted Educational Intervention. | Formatting/organization request satisfied. Bibliographic validity and claims are separate checks. |
| 12 | Use cases shared by two or more actors | Figure 10, p. 35, visibly connects multiple actors to common viewing use cases, including progress/report viewing. | Shared-interaction request satisfied. This does not establish that every depicted permission matches current software. |
| 13 | Align WBS with methodology and remove unnecessary components | p. 25 says PADIM; p. 23 lists seven Agile phases; p. 26 says six phases, initially listing five. Figure 7 shows seven columns, with the final maintenance-like column incorrectly headed DESIGN; numbering repeats 3.x and 6.3. | Not satisfied consistently. Use the approved methodology's phase names/count, rename the final column appropriately, correct numbering, and review task scope. |
| 14 | Revise/reorganize Use Case Diagram | Figure 10 exists as one combined four-actor diagram with shared use cases. Crossing lines and overlapping review/approval concepts remain; scope/release qualifications and onboarding are absent. | Combined structure present; partially aligned. Historical revision itself cannot be proven without a before/after figure. Reconcile associations with actual role permissions and improve legibility. |
| 15 | Align DFD with CFD | Figures 11-12, pp. 36/38, contain the same four actors, but flow balancing is incomplete: CFD has Admin -> system Student Record Information; DFD process 1.0 shows Student Information from Teacher, without the matching Admin record input. DFD also returns Updated Student Records from Generate Reports to Admin, unlike the CFD outputs. | Partial. Reconcile external inputs/outputs across both diagrams and the implemented permissions; correct prose on p. 37 to match the actual single database store drawn. A single D1 database store is not inherently an error. |
| 16 | State nonfunctional requirements | pp. 31-34 explicitly list performance, reliability, usability, security, compatibility, maintainability and portability, with 5-second/3-second targets. | Requirement to state them is satisfied. Targets still need measurable conditions and acceptance evidence; listing them does not prove achieved performance. |

## Important additional paper/system mismatches

1. **Model table error, pp. 53 and 61:** MobileNetV2 Normal precision is printed
   as 88.42%; the selected validation CSV and p. 52 narrative give **84.42%**.
   The matrix counts give 65/(65+12)=84.42%. Keep accuracy 88.06%, Normal recall
   94.20% and Normal F1 89.04% distinct.
2. **Wrong MobileNet training figure, p. 56, Figure 18:** visually matches
   `output/mobilenet-finetune-2026-11-10/finetuning_accuracy_loss.png`, the separate
   three-epoch fine-tuning experiment. The caption/text calls it original
   MobileNetV2. That fine-tuned copy was not the selected original model. Remove
   it from the original-model results or explicitly label it as an excluded
   experiment with its own results. Do not present it as the original training run.
3. **Figures 21/22, pp. 58-59:** Figure 21 contains the grouped accuracy/High
   Potential precision/recall/F1 comparison; Figure 22 contains only validation
   accuracy. The surrounding prose describes Figure 21 as accuracy and Figure 22
   as class-wise metrics. Align figure references/captions and actual contents.
   Neither inspected figure is a confusion matrix.
4. **Table 11, p. 61:** headings say averages but rows contain class-specific
   metrics without class labels. Add a Class column and use precision/recall/F1
   headings; show model-level validation accuracy separately. Correct RestNet50
   and the earlier CCN typo. Remove the old unfinished/contradictory paragraph
   spanning pp. 58-59: its high-recall/low-precision description conflicts with the
   updated selected results.
5. **Validation versus deployed default:** the selected 134-image validation
   comparison is correctly identified as validation in pp. 52-62 and correctly
   ranks MobileNetV2 first. Retain this improvement. Add the distinct previously
   used 136-image test comparison (85.29%, 78.68%, 86.76%; ResNet displayed as
   86.77% from the stored rounded value) and explain the recorded production
   ResNet50 default/all-model availability. This review did not recheck production.
6. **Architecture/requirements, pp. 28-31, 62, 65-66:** MySQL, guest signup,
   Low Potential, React.js web frontend and Node.js backend conflict with the
   current hosted Vue admin/Expo app/Flask/Supabase design. Replace them throughout
   and reconcile the architecture image and data dictionary, not only prose.
   The Supabase Auth/security update on pp. 63-65 is an improvement; the table's
   universal logging wording still exceeds the narrower supported-activities prose.
7. **Screening wording, pp. 5-8:** the disclaimer on p. 5 conflicts with diagnose
   in the objective and definitive diagnosis/guaranteed identification on p. 7.
   Use the implemented screening scope consistently. Describe the percentage as
   a model score rather than a demonstrated probability of the child having a
   condition. This is a paper-to-software consistency finding, not a clinical review.
8. **Dataset/reference evidence:** pp. 46-49 retain provenance/labeling claims
   needing original documentation; p. 49 implies final-only test use, while project
   records show reuse. Writer separation remains unverified. References starting
   on pp. 66-67 reuse labels [3]/[4] for different works; fix numbering and body
   references. External sources were not opened or verified in this review.

## Verification and next steps

Extracted all 75 pages with the existing local PDF.js tooling. Rendered pages 10,
11, 12, 24, 26, 30, 35, 36, 38, 53, 56, 57, 58, 59 and 61; visually inspected
the relevant RRL, methodology, WBS, use-case, CFD/DFD and selected model-result
pages. Inspected diagrams again at higher resolution. Compared MobileNet figure
and table values with saved experiment/selected-validation evidence. No model,
database, app, manuscript or hosted configuration changed; no fresh live tests.

Priority: align WBS/timeline with the retained Agile methodology, fix account onboarding and Initial/Follow-up wording;
correct model tables/figure provenance and explain the deployed default; align
objectives/scope/architecture/diagrams; then proofread references and collect the
remaining installed-app and measured nonfunctional acceptance evidence.
