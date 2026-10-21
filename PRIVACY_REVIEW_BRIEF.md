# GraphiScan privacy wording: inputs for review

Status: **No approved wording available**, confirmed by the user on 2026-10-20.
This is a project input brief, not agreement text, approval or a legal conclusion.
Nothing here should be published as consent or inserted as a current agreement.

Subsequent user decision (2026-10-20): use this as the basis for a **temporary
fictional-account test notice**, revisable later. The actual temporary text is
[test-notice-v1.txt](graphiscan/api/test-notice-v1.txt), with the technical flow in
[PRIVACY_ACCEPTANCE.md](graphiscan/api/PRIVACY_ACCEPTANCE.md). That limited test
authorization does not fill the unresolved real-use decisions below or approve
real student-data collection. The brief itself remains unpublished.

## Verified product facts for the eventual draft

- GraphiScan screens handwriting for possible dysgraphia-related difficulty; it
  does not provide a clinical diagnosis. The active predictor is binary.
- The current app handles user accounts, linked student information, handwriting
  images, screening results, expert reviews, reports and activity/audit records.
  The final field inventory still needs review against the deployed release.
- The target account flow is team-issued credentials, required first-login
  password change, then the approved versioned privacy agreement. User-run hosted
  password checks passed; agreement publication/acceptance is not implemented.
- Record access is role- and relationship-dependent. The intended parent release
  rule is linked students' expert-Validated results only; real resource endpoints
  and storage authorization remain separate migration work.
- Current Vue/MySQL/Flask paths remain active. Supabase Auth/PostgreSQL is a
  disposable test foundation. Private hosted image storage, client cutover and
  production hosting are targets, not completed operational facts.

## Decisions needed before wording can be approved

| Topic | Information to supply or confirm |
| --- | --- |
| Responsible organization | School/institution/project owner to name and its role in operating the system |
| Contact | Actual contact for privacy questions and record requests; no invented address |
| Data inventory | Exact deployed fields, account roles, student linkage, image/result/review/report data and logs |
| Purposes | Approved screening, expert review and reporting purposes; separately decide whether research/model training or other reuse is permitted |
| Participants and permissions | How staff onboarding, school authorization and parent/guardian permissions for student participation are handled; an adult user's account agreement does not itself record a guardian's decision for a child |
| Access and recipients | Who receives which data, who operates services, final hosting providers/regions and any approved exports/sharing |
| Retention and deletion | Real durations, record categories, backups/downloads, deletion/request workflow and responsible owner; currently unresolved |
| Requests and choices | Actual process for questions, corrections, access/withdrawal/deletion requests and how participation choices affect use; do not promise an unimplemented capability |
| Approval and publication | Named authorized reviewer, final reviewed wording, version, approval record and publication date |

These are unresolved project questions, not assertions that a particular legal
basis, retention period, consent mechanism or jurisdiction has been approved.
Legal or institutional requirements must be established by the responsible review.

## Engineering work while wording is pending

- Keep missing-agreement behavior closed: v1 bootstrap reports
  `agreement_unavailable`; normal protected features remain denied. Do not seed
  placeholder wording or invent an acceptance row to bypass the gate.
- Generic login/logout, explicit refresh/session checks and failure/concurrency
  coverage can proceed independently, with synthetic identities and existing
  fictional test fixtures. Passing first-change checks should not be repeated
  against the now-changed fixture without adapting expectations.
- Plan and test acceptance mechanics against clearly fictional fixtures. Final
  agreement publication, real acceptance and client cutover wait for approved
  wording and the corresponding reviewed implementation.

Related: [API contract](API_CONTRACT.md), [system map](KNOWLEDGE.md),
[resume checkpoint](RESUME.md), [password evidence](graphiscan/api/PASSWORD_CHANGE.md).
