# Final screening summary and conclusion

2026-11-10 update: User reports installing migration031; installation has not been independently verified. Updated mobile source is local, not published. The change allows a linked parent to read a current finalized report including Flagged screenings; individual screening/report access remains Validated-only. Run the read-only `031_parent_final_report_preflight.sql` to check installation; all flags should be true. Do not rerun 030. Publish the updated mobile source separately.

User subsequently reports all three 031 preflight flags true. Parent account end-to-end acceptance remains pending.

Local implementation, 2026-11-09. Owner reports migration030 succeeded; independent
read-only hosted verification passes all six flags and all three exact function
body comparisons, including Initial-only finalization. Do not rerun030.
API/mobile changes are not published and no new APK exists.
The current published APK1.0.2 does not include this feature.

## Workflow

Student/Child details and Screening history open **Final summary and conclusion**.
The page brings together every official Initial and Follow-up screening, its model
label, expert observations and recommendation. It does not calculate improvement
from model scores. Labels remain binary Normal / High Potential.

The expert writes two fields: **Expert conclusion** (screening observations and
overall conclusion together) and **Recommendation** (what should happen next).
They preview the text and explicitly select Finalize report. Requirements:

- Current expert access to the complete history through existing school/grade
  responsibility (migration025), not a new per-result assignment rule.
- A reviewed Initial screening. Follow-ups are optional: the expert may conclude
  after the Initial, or after any number of Follow-ups.
- Every included screening reviewed as Validated or Flagged with an author.
  A Flagged review can support a conclusion recommending further assessment;
  finalization does not change any individual review/release status.
- The latest review records Follow-up needed = No. That exposes **Finalize
  screening** on the expert result; it opens the summary/conclusion form. No
  automatic final report is created by toggling the review switch alone.

The immutable report records author/name/date, conclusion text and the full
ordered history snapshot. No generated recommendation, diagnostic conclusion,
new screening class, PDF export or hard deletion is added.

A new completed screening, changed review, changed assignment revision or student
revision makes the old snapshot noncurrent. Monitoring reopens and the old final
text is withheld from this endpoint. A new expert conclusion appends a revision;
older rows stay immutable. Screenings keep their existing Initial/Follow-up types;
there is still exactly one Initial per student. Finalized means the reviewed
period has a conclusion; it does not permanently block future uploads.

Reader presentation remains blank until an expert saves a current final report:
no student name/grade heading, Monitoring prose or provisional screening contents
are substituted for that report. Expert workspace retains its preparation/form
controls. Two actual expert fields appear after finalization. Routine refresh
buttons are removed; use pull-to-refresh or error-only retry.

Teachers can read current owned/scoped reports. Experts use existing school/grade
scope. Linked parents can read a current finalized report only when **every**
included screening is currently Validated. An unpublished/stale/inaccessible
parent final report returns the same404. Admin/researcher reads retain the
existing assignments.manage school/global scope. No new user permissions.

## API and storage

- `GET /api/v1/students/{student_id}/final-report`: scoped current report state.
- `POST /api/v1/students/{student_id}/final-report`: expert-only finalization,
  requiring Idempotency-Key and exactly summary/conclusion/next_steps,
  expected_revision (initially0), history_fingerprint from GET. Text1-10000
  characters per field; no client-supplied author, screening list or state.
- The two-field mobile form keeps the installed030/API format compatible: the
  combined conclusion populates both legacy summary and conclusion; Recommendation
  populates next_steps. No migration or API change is needed for this simplification.
  Read views show one Expert conclusion section, merging distinct legacy summary
  and conclusion text while displaying identical text only once, plus Recommendation.
- POST body limit128KiB. No query parameters. Errors are bounded/private.
- New final_screening_reports table is RLS-protected with no client/reader/writer
  table or sequence grants. Fixed-path owner functions provide separated reader
  and writer execution; internal context helper has no application-role execute.
- Existing authenticated directory/history capabilities supply projections and
  gates. All pages are collected using the reader's limit+1 seam, then compared
  with the complete official screening count. Partial scope cannot silently form
  a whole-history report; no Storage paths are returned.
- Digest binds student revision and ordered screening/review/assignment revisions
  and values, excluding display-only review author names. Final author name is
  saved at finalization. Renaming an expert does not reopen monitoring.
- Finalization locks existing results before the student (matching review lock
  order); upload completion also locks the student. It rechecks gates/history,
  fingerprint and final revision under those locks, writes one immutable snapshot
  and audit row in the same transaction. Exact retries return the same current
  snapshot; changed payload/key reuse or stale history fails409.
- Mobile retains the exact request key/body after an uncertain response, blocks
  accidental departure, and offers explicit same-request retry. Definitive
  errors require refreshed review; no automatic POST replay. Draft/key recovery
  after process death is not implemented. Current GET proof can reconcile an
  uncertain save. Preview is invalidated when a refreshed history changes.

The legacy MySQL/Flask report route and Vue user/admin routes were inspected.
They remain per-screening flows; this feature targets the active hosted API and
Expo app. No legacy table, stored label, predictor or existing access rule changes.
Admin has API read access but no new dedicated final-report web page in this slice.

## Activation

1. Completed: owner applied `db/postgres/030_final_screening_reports.sql` after029.
   Do not rerun it or earlier migrations. This creates schema/functions, not student records,
   user grants, consent, model defaults or credentials. Do not edit installed
   functions manually or grant direct table access.
2. Completed: six preflight flags and exact body comparisons all pass through
   `tools/check_v1_final_reports.py --connect`. This is read-only metadata/source
   evidence and returns no application rows. No further migration required.
3. Publish/restart the matching API, then distribute a rebuilt APK containing the
   new screen. Until those steps, do not claim this feature is active on1.0.2.
4. Use controlled fictional records to check Initial -> Follow-up -> expert
   finalization -> teacher/parent reading; Flagged/private denial, review changes,
   new upload/reopened monitoring and explicit uncertain-save retry.

## Verification

Recorded local evidence is in CHANGELOG.md. SQL checks run the actual migration
and functions in disposable PGlite, never the hosted database. Python tests mock
the repository/identity boundary. Browser/native previews use in-memory fictional
records and do not establish hosted writes or installed release-APK acceptance.
Real multi-connection contention and process-death recovery remain unverified.
