# Student details before screening history

Local mobile implementation, 2026-11-06. Tap a student/child in the Expo directory to
open Student details (Child details for parents), showing the student name,
school name, grade/age and current linked parent's name, or No parent linked.
Screening records are requested only after View screening history is selected.
Teachers retain an explicit Edit student action; experts and parents have none.
Student rows have one details action. Teachers edit from the details screen.

GET /api/v1/students and /api/v1/students/{student_id} retain their existing
authorization and pagination. Installed migration028 adds optional school_name and
nullable parent_name to their JSON projection, resolving only the school and
parent attached to an already-authorized student. It creates no account directory,
changes no student/parent links or permission grants, and adds no screening data.
The parent name is returned only when the linked profile has role parent. Existing
teacher ownership/grade, expert school/grade, parent linkage, admin school grants,
session and onboarding checks remain in the same SQL statement. Parent screening
history still uses the existing Validated-only release rules.

Migration db/postgres/028_student_display_names.sql was applied by the owner after027.
The read-only db/postgres/028_student_display_names_preflight.sql returns five true
flags. The migration
normalizes both comparison/replacement literals and the existing function for
LF/CRLF text and supports exact reruns. Unknown reader projections fail without
changing the function. No records are seeded. The existing Python DirectoryService
passes the additional fields through, so this change needs no new endpoint or
API restart. Refresh current local Expo source. Owner reports applying028, and
read-only hosted function metadata independently verifies all five preflight flags
and exactly one new-projection match. Do not rerun028 to resume. The mobile source
changes are not yet published.

Until name metadata is available, the screen identifies an existing link as
Parent linked and labels an unavailable school name explicitly; it never invents
a person/school name or displays account IDs as names. Failed first reads offer
retry without history actions. Returning from editing refreshes the detail;
authorization/not-found failures clear cached details and actions.

Verification: TypeScript,20 mobile tests,11 existing directory API tests,
Android/web exports,654 contract assertions and all isolated SQL suites pass.
The32 new SQL checks cover projection/schema, all relevant roles and scopes,
current-link names, unlink access, session/privacy gates, ACL retention,
LF/CRLF combinations and migration reruns/rejection.42 fictional browser checks
at320/390 cover the three roles, details-first navigation, explicit history,
edit authority, retry, lost access and removed-parent refresh, without real writes.
The hosted reader was independently checked read-only after activation: the new
projection matches once, and scope/ACL checks remain intact. A signed-in teacher's
native details screen was observed showing current school and linked parent names;
the user confirmed it works. Expert and parent native detail acceptance and the
full screening flow remain pending. This Expo Go run is not a standalone APK.
