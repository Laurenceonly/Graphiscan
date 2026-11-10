# Local release review - 2026-11-05

Implemented: aligned Add/Edit actions, consistent cards and compact layouts,
stable chart switching, fixed search outside the Progress scrollbar, shared fades,
local-font startup, circular breakdown, current login mockup, readable audit actions,
recoverable Results errors and current school/grade expert lists.

The administrator assigns expert school and grade scopes. Prepared migration025
authorizes every current/future student and screening in those scopes, including
history, images and reviews. Reassignment revokes sessions and old scope access.
Historical review authorship stays intact. Parent release still requires a linked
student and Validated review; teacher ownership remains enforced.

| Verification | Result |
| --- | --- |
| Python suite | 293 tests pass, one Windows symlink skip |
| API contract | 644 checks pass |
| Isolated PostgreSQL suites | All pass, including 34 expert-scope and 54 assignment checks |
| Shared client / mobile tests | 27 / 18 pass |
| Admin / retained user web builds | Pass |
| Mobile TypeScript | Pass |
| Responsive panels and modals | 107 checks, eight viewport sizes from320x568 to1920x1080, including568x320 |
| School/student workflows | 126 checks |
| Account / assignment workflows | 29 / 40 checks |
| Results read-error recovery / session restore | 15 / 30 checks |
| Motion and reduced motion | 70 checks |
| Teacher upload, expert review, parent release/history | 79 checks with fictional API responses |
| Add alignment | 12 page/viewport combinations |
| Fonts / circle / login mockup | 35 checks |
| Static layout/type detector | No findings |

Browser fixtures exercise cancellation, permission loss, stale responses, conflicts,
uncertain writes and retry behavior where supported by the relevant flow. They
intercept APIs and use fictional identities and records. SQL suites use disposable
PGlite databases; they do not apply migrations to Supabase. Browser upload tests
simulate inference and private storage, so they establish client behavior only.

Migration001-025 metadata and all52 latest function bodies are independently
verified installed after the owner ran025. Its four read-only preflight checks
pass. The second run hit the original guard; the local migration now supports
safe repeated runs, covered by isolated tests. No further owner run is needed.
Confirm real authorized expert reassignment/review and parent release next.

Still open: controlled hosted Auth/inference/Storage acceptance, installed Android
testing, and deployment verification. No real student/account changes or push were
performed during this review. Existing unrelated working-tree edits must be
reviewed before selecting a publication commit.
