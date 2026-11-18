## Current PDF review - 15 November 2026

User confirms Agile as the methodology. Retain the Agile figure/narrative;
remaining methodology work is WBS/phase/timeline consistency. The earlier Hybrid
replacement task is superseded by this explicit direction.

The user supplied the current 75-page `GraphiScan (1).pdf`. Use
[DEFENSE_CURRENT_PDF_REVIEW.md](DEFENSE_CURRENT_PDF_REVIEW.md) for verified current
pages, satisfied requests and remaining corrections. Older unchecked items/page
references below are not a fresh assessment of that PDF. In particular, four
italicized RRL themes, shared use cases and stated nonfunctional requirements
are present; methodology/WBS/onboarding/Follow-up, diagrams and model figure/table
corrections remain. No PDF edits made.

# GraphiScan Paper Revision Checklist

Use this checklist to revise the existing GraphiScan paper against the current system and the June 1, 2026 defense minutes. The page numbers below refer to the 76-page PDF reviewed on November 10, 2026; the printed page numbers in the defense minutes may differ. Check the editable paper and final diagrams as you make changes. Items are revision tasks, not claims that the changes have already been made.

## 1. Title and wording throughout the paper

- [ ] Discuss the title with your adviser. Use **screening** rather than diagnosis where permitted, and explain that GraphiScan supports professional assessment rather than replacing it. Check the cover, objectives, significance, definitions, results and conclusion for consistent wording.
- [ ] Replace claims that the system diagnoses dysgraphia, guarantees identification, or provides treatment with accurate descriptions of preliminary screening. A Normal result does not rule out a difficulty.
- [ ] Use the current labels **Normal** and **High Potential**. The defense minutes mention Low Potential as an example of a highlighted classification; it is not a current output.
- [ ] Describe the percentage as the **model's High Potential score for the submitted image**, not the probability that a child has dysgraphia or the model's accuracy. The current decision rule classifies scores of at least 0.75 as High Potential.
- [ ] Remove claims that the AI automatically gives personalized recommendations. Explain that an authorized expert writes remarks and recommendations based on their review.

## 2. Background of the Study

**Where:** PDF pages 3–5; the defense minutes identify pages 2–5.

- [ ] Explain the problem, the research gap supported by the literature, and why a screening and record-management tool may help its intended users.
- [ ] Check the evidence and citations for claims about dysgraphia, existing tools and AI. Avoid saying no automated systems exist unless the cited evidence supports that claim.
- [ ] Remove claims that GraphiScan measures individual handwriting features, transcribes text or provides intervention unless those capabilities and evidence can be demonstrated.

## 3. Objectives

**Where:** PDF page 6 and related sections throughout the paper.

- [ ] Name **MobileNetV2, EfficientNetB0 and ResNet50**, and state that their purpose is to classify handwriting images into the two screening labels. Check for the incorrect name ResNet50V2.
- [ ] Include expert validation as the panel requested, and explain that expert recommendations should be justified by the review or analysis.
- [ ] Explain the dataset, threshold and metrics for each comparison. State that the production registry identifies fine-tuned ResNet50 as default based on the test comparison, while MobileNetV2 leads the validation comparison.
- [ ] Align the objectives, results and conclusion: each conclusion should answer an objective and be supported by the reported evidence.

**Suggested general objective for adviser review:** Develop GraphiScan, a role-controlled system that supports preliminary screening of handwriting images for possible indicators associated with dysgraphia and enables expert review and record management.

## 4. Scope and limitations

**Where:** PDF pages 8–9.

- [ ] State that the intended student scope is elementary Grades 1–3 and that students are grouped by school and grade, as requested in the defense minutes. Distinguish intended users from the actual participants and dataset used in the study.
- [ ] Explain that the hosted workflow depends on internet access. Describe the actual limits of access by role and student relationship.
- [ ] Explain that the expert, not the model, provides recommendations. Screening history can be reviewed over time but does not automatically prove improvement.
- [ ] State the dataset and evaluation limitations described in section 9 below; do not claim the system has been clinically validated without evidence.

## 5. Review of Related Literature and comparison table

**Where:** PDF pages 10–21; the minutes identify literature pages 10–12.

- [ ] Group the literature into **three or four themes** with italicized headings, as the panel requested. Choose themes that fit the sources actually used.
- [ ] Verify every cited source and make sure each claim is supported. Check authors, publication details, links and the required citation style.
- [ ] Revise the comparison table so it only credits GraphiScan and other systems with features supported by evidence. Remove unsupported ticks for transcription, automatic intervention or diagnosis.
- [ ] Define screening, model score, expert review, Pending, Validated, Flagged, Initial and Follow-up consistently with the implemented workflow.

## 6. Methodology and project plan

**Where:** PDF pages 22–28; the defense minutes refer to the methodology image on page 24 and WBS on page 26.

- [x] Retain **Agile**, confirmed by the user on November 15; the current PDF figure and methodology narrative use Agile. The earlier Hybrid replacement task is superseded.
- [ ] Make the figure, methodology narrative, Work Breakdown Structure and Gantt chart use the same phases. Remove unnecessary WBS components and distinguish planned work from work actually completed.
- [ ] Correct the architecture description: the current hosted design uses an Expo Android app, Vue admin web app, Flask API, Supabase authentication and PostgreSQL, private image storage, and server-side inference. Older Flask/MySQL and user-web paths also exist; do not present them all as one current deployment.

## 7. Requirements and user workflow

**Where:** PDF pages 29–34; the minutes refer to nonfunctional requirements on pages 34–36.

- [ ] State that authorized administrators or researchers issue accounts. Users change their initial password and accept the privacy agreement before accessing features. Do not say guests self-register. Account agreement does not by itself establish participant consent.
- [ ] Explain the first completed screening as **Initial** and later completed screenings as **Follow-up**. Follow-ups are optional before a final report when the applicable conditions are met.
- [ ] Describe what teachers submit, how assigned experts review and record recommendations, and what linked parents can access. Individual parent screening access is limited to Validated results; the newer current final-report rule differs and still needs end-to-end verification.
- [ ] Replace unsupported requirements for automatic improvement assessment, tailored AI advice, image transcription, and unverified preprocessing with testable requirements reflecting actual behavior.
- [ ] List nonfunctional requirements such as access control, usability, reliability and response time. Label five-second and three-second figures as targets unless measured under documented conditions; report the test device, connection, sample size and failures when available.

## 8. Diagrams and data descriptions

**Where:** PDF pages 34–45; the defense minutes refer to use cases on page 38 and CFD/DFD on pages 39 and 41.

- [ ] Reorganize the Use Case Diagram and include interactions shared by two or more actors, while showing only actions each role is authorized to perform.
- [ ] Align the Context Flow Diagram and Level 1 Data Flow Diagram: match external actors and inputs/outputs, use distinct labels for separate stores, and show private images separately from screening records.
- [ ] Update the architecture diagram to match the current hosted stack and show authentication, database, private storage and inference.
- [ ] Decide whether the ERD and data dictionary are conceptual or physical. If physical, rebuild them from current PostgreSQL migrations and verify tables, fields, types, keys and relationships. Remove unsupported claims such as automatically generated PDF reports.
- [ ] After redrawing, update captions, figure numbers, cross-references, explanations and screenshots. Check every diagram visually against the actual workflow.

## 9. Dataset, models and results

**Where:** PDF pages 46–63, especially Figures 18–22 and Table 11.

- [ ] Verify dataset source, permission, labeling, participant characteristics and preprocessing before retaining those claims. The recorded split contains 627 training, 134 validation and 136 test images.
- [ ] State that no exact image hashes overlapped across splits, but writer-level separation and transformed duplicates were not verified. The test images were used in previous comparisons; do not call this an untouched independent test.
- [ ] For Algorithm Selection, use the user's chosen validation comparison: original MobileNetV2 (88.06%), fine-tuned EfficientNetB0 (83.58%), and fine-tuned ResNet50 (85.82%), all measured on the same 134-image validation split at 0.75. Use its class-wise metrics from the selected validation package. Label these as validation results because the split was used to choose model versions and fine-tuning weights; do not describe them as test results or independent validation.
- [ ] Report the separate selected-version evaluation on the previously used 136-image test split: MobileNetV2 85.29%, EfficientNetB0 78.68%, ResNet50 86.76% (118/136); the app displays 86.77% from its rounded stored value. These are not independent clinical results. The fine-tuned models are deployed; historical 0.50-threshold figures are a different comparison.
- [ ] Correct the ResNet contradiction: Table 11 reports 89.03% while the text reports 86.03%. Return to the matching source evidence instead of guessing which number belongs in the table. Also reconcile the EfficientNet Normal metrics and complete the unfinished sentence on PDF page 53.
- [ ] Report class-specific precision, recall and F1, plus false positives and false negatives, where supported. Avoid claiming a model is best on every metric when the evidence shows a tradeoff.
- [ ] State that MobileNetV2 ranks first on validation accuracy and class-wise F1, while fine-tuned ResNet50 is the current production default because it has the highest displayed test accuracy. Explain the data reuse and unverified writer separation; do not claim a universal winner. Use the proposed manuscript text in PAPER_SYSTEM_ALIGNMENT.md.

## 10. Implementation, conclusion and references

**Where:** PDF pages 63–76.

- [ ] Replace outdated React, Node.js and MySQL descriptions where they are presented as the current hosted stack. Distinguish source implementation, local testing and deployed behavior.
- [ ] Keep specific claims about MFA, encryption algorithms, logging coverage, backups and automatic retraining only when supported by actual configuration or operational evidence. Otherwise remove them or label them as proposed.
- [ ] Limit the conclusion to demonstrated results and state remaining limitations. Do not claim clinical effectiveness, guaranteed detection or completed acceptance without evidence.
- [ ] Verify all references, citations, figure labels, table numbering and cross-references; proofread the entire paper after revisions.

## Evidence to collect before submission

- [ ] Test the authenticated live model chooser and a screening with each model. Production registry versions and the ResNet50 default were verified on 13 November; inference acceptance remains open.
- [ ] An authorized teacher-to-expert-to-linked-parent walkthrough, including Initial, optional Follow-up and applicable report access, without exposing private student data.
- [ ] Measured response-time and usability results, including conditions and sample sizes.
- [ ] Dataset provenance, permissions, labeling and writer separation; approved privacy, retention and participant-permission arrangements.
- [ ] Adviser approval of title, objectives, methodology figure and WBS, plus updated screenshots and diagrams.

## Recommended order

1. Agree on the title, scope, objectives and methodology with your adviser.
2. Select one model evidence set and revise all results together.
3. Revise the system description, requirements, diagrams and screenshots.
4. Update the background, themed literature, conclusion and references.
5. Collect missing evidence and perform a final page-by-page check.

Source material: the supplied GraphiScan PDF; `GraphiScan_Defense_Minutes.md`; `PAPER_SYSTEM_ALIGNMENT.md`; current project source and recorded evidence as reviewed in that guide. The defense minutes' Action/s Taken column records reported actions and does not independently establish that the manuscript was revised.
