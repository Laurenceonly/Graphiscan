# GraphiScan manuscript revision list - top to bottom

**16 November update:** Follow the user's supplied consolidated revision log
by section heading; see [current guidance](MANUSCRIPT_REVISION_LOG_GUIDANCE.md).
It supersedes conflicting suggestions and the instruction below to restart at
item 1. Reported prior edits need verification in the working manuscript, not
automatic repetition. Preserve the log's explicit retention decisions.

Saved 15 November 2026 at the user's request for later work. **Planned work;
the manuscript has not been edited.** Resume from item 1 and proceed in order.

Current manuscript: `C:/Users/MY_PC/Downloads/GraphiScan (1).pdf`, 75 pages.
All page references are PDF viewer pages. User confirms **Agile**; keep Agile,
not the earlier Hybrid replacement task. Companion evidence and all 16 defense
requirements: [DEFENSE_CURRENT_PDF_REVIEW.md](DEFENSE_CURRENT_PDF_REVIEW.md).

## Revision checklist

1. [ ] **Page 1 - Title.** Use one approved title throughout. Resolve cover
   "Using Convolutional Neural Networks" versus body "Using Deep Learning
   Techniques"; align chapter introductions, objectives and figure descriptions.

2. [ ] **Pages 2-5 - Background.** Organize problem -> existing limitations ->
   specific evidenced gap -> GraphiScan's contribution. Qualify "AI efficacy is
   unquestionable" and "no automated detection systems." Describe the percentage
   as a model score for the image, not an established probability of the child
   having dysgraphia. Do not claim individually measured handwriting features.

3. [ ] **Page 6 - General objective.** Replace diagnosis wording with preliminary
   handwriting screening. Align with classification, expert review, justified human
   recommendations and record management.

4. [ ] **Page 6 - Specific objectives.** Correct ResNet50V2 to ResNet50. Name all
   three models and their purpose. State all three are available with a default,
   rather than implying only one is deployed. Retain expert validation and link
   recommendations to expert analysis. Claim efficiency evaluation only if measured.

5. [ ] **Page 7 - Significance.** Remove or qualify definitive diagnosis,
   guaranteed identification and ensured intervention. Match stakeholder benefits
   to actual features; identify recommendations as expert-written.

6. [ ] **Pages 8-9 - Scope/limitations.** Keep Grades 1-3; explicitly group students
   by school and grade. Clarify Android teacher/expert/parent versus admin web,
   internet dependence, binary Normal/High Potential and expert recommendations.
   History supports monitoring without automatically calculating improvement.
   Distinguish target participants from dataset participants; fix offline wording.

7. [ ] **Pages 10-12 - Literature.** Keep the four italicized themes, already
   present. Proofread and qualify unsupported unbiased-AI claims. Check each
   citation against its associated statement.

8. [ ] **Pages 13-19 - Related works/comparison.** Recheck all feature ticks and
   comparisons. Correct unsupported transcription, automatic intervention,
   personalized AI advice and separately measured handwriting-feature claims.
   Align table, discussion and actual capabilities.

9. [ ] **Pages 20-22 - Definitions.** Align screening, model score, human
   recommendation, Normal/High Potential, Pending/Validated/Flagged,
   Initial/Follow-up, and individual versus final whole-history report terms.

10. [ ] **Pages 22-24 - Agile.** Keep Agile and Figure 5. Explain actual iterations,
    testing and feedback. Match WBS/Gantt phase names; distinguish done from planned.

11. [ ] **Pages 25-26 - WBS.** Remove conflicting PADIM reference. Align phase
    count/text/figure. Rename final Design column to Maintenance. Fix repeated
    maintenance 3.x numbering and duplicate 6.3. Align tasks with actual Agile work;
    remove unnecessary or unsupported activities.

12. [ ] **Pages 27-28 - Gantt.** Match methodology/WBS phase names; verify task
    order, dates and completion claims against actual work.

13. [ ] **Pages 28-30 - Architecture/Figure 9.** Show Expo Android, Vue admin,
    Flask API, Supabase Auth, PostgreSQL, private image storage and server-side
    inference. Remove obsolete guest signup, current-hosted MySQL and Low Potential.
    Update both image and prose.

14. [ ] **Pages 30-31 - Functional requirements.** Replace self-registration with
    admin issuance -> temporary-password change -> privacy acceptance -> authorized
    workspace. Describe actual preprocessing, selectable models, expert review and
    scoped report access. First completed screening is Initial; later ones Follow-up.
    Remove unsupported educational-content/improvement automation.

15. [ ] **Pages 31-34 - Nonfunctional requirements.** Keep the existing section.
    Make targets testable with device, connection, image size and concurrency
    conditions. Five/three-second figures remain targets until measured. Do not
    claim archiving, universal compatibility or concurrent performance without proof.

16. [ ] **Pages 34-35 - Use cases.** Keep shared-actor interactions, already
    present. Improve label/line readability, reconcile actor permissions and
    overlapping validation/approval use cases. Explain school/link/release scope.

17. [ ] **Pages 35-38 - CFD/DFD.** Balance external inputs/outputs, particularly
    Admin Student Record Information and Updated Student Records from Generate
    Reports. Check arrow directions, labels, permissions and matching prose.
    A single D1 database store is acceptable when used consistently.

18. [ ] **Pages 38-45 - ERD/data dictionary.** Decide conceptual versus physical.
    If physical, use actual PostgreSQL tables/types/keys/relationships, including
    schools, links, versions, reviews and final reports. Remove unsupported fields
    and generated-PDF claims. Reconcile Initial/Follow-up report terminology.

19. [ ] **Pages 46-49 - Dataset/preprocessing.** Verify original source,
    permissions, labeling and participant details. Binary total 897: train 627,
    validation 134, test 136. Disclose prior test reuse and unverified writer
    separation. Match exact training/runtime preparation; fix augmentation wording.

20. [ ] **Pages 52-54 - Algorithm selection.** Keep selected validation accuracies:
    original MobileNetV2 88.06%, fine-tuned EfficientNetB0 83.58%, fine-tuned
    ResNet50 85.82%. Correct MobileNet Normal precision to 84.42% in p. 53 table;
    correct CCN to CNN. Separate validation winner from production-default evidence.

21. [ ] **Pages 55-57 - Training graphs.** Figure 18 on p. 56 belongs to the
    separate MobileNet fine-tuning experiment, not the selected original model.
    Remove or accurately label it as a separate excluded experiment. Verify every
    curve's model version, run and metric threshold.

22. [ ] **Pages 58-60 - Charts/discussion.** Figure 21 shows grouped metrics;
    Figure 22 shows validation accuracy only. Align descriptions/captions/references.
    Remove old unfinished and contradictory high-recall/low-precision prose.
    Include actual confusion matrices if claiming to present them.

23. [ ] **Pages 61-62 - Table 11/findings.** Correct MobileNet Normal precision
    88.42% to 84.42%, and RestNet50 to ResNet50. Add class labels; remove Avg from
    class-specific metric headings. Separate accuracy from class metrics. Retain
    MobileNet validation winner; explain all three selectable production models and
    ResNet50 default using the distinct previously used test comparison:
    MobileNet 85.29%, EfficientNet 78.68%, ResNet 86.76% (displayed 86.77% from the
    stored rounded value). Do not mix test and validation populations/rankings.

24. [ ] **Pages 62-66 - Implementation/security/maintenance.** Replace obsolete
    React web/Node/MySQL stack descriptions. Keep Supabase Auth correction. Align
    logging statements with actual coverage. Label retraining, backup and maintenance
    schedules as plans unless operational evidence establishes them.

25. [ ] **Pages 66-75 - References/final proofreading.** Fix duplicate reference
    labels, including reused [3]/[4], and all affected body citations. Verify sources,
    figure/table numbering, captions, terminology, spelling and cross-references.

## Handoff

User requests saving now and doing revisions later. No manuscript edits are
authorized to begin in this save-only turn. When resumed, use the current PDF and
this sequence; preserve Agile and keep planned edits distinct from completed work.
An editable manuscript will be needed for direct Word/Google Docs editing; do not
claim the PDF or manuscript changed merely because this checklist is saved.

Highest-impact corrections: objectives, WBS, architecture, account/screening
workflow and model-results errors. Separate installed-app/hosted acceptance and
measured nonfunctional evidence remain outstanding as recorded in the audit.
