# GraphiScan afternoon presentation rehearsal

Latest steering: user asked to stop focusing on guest demo and plans to remove
it. Do not perform the guest inference step described historically below.
Core teacher/expert/parent/admin requirements and implementation take priority;
actual guest feature/role removal is planned, not completed. Keep the existing
screen confirmations as evidence without extending optional-demo rehearsal.

Status 2026-10-20: user confirmed the existing admin dashboard loaded after
sign-in. Both Vue builds, all 26 read-only local API checks and three local HTTP
entry points passed. Current authenticated browser navigation has not been
independently inspected: the browser connector returned no available browsers.

## Quick screen check

Using the already signed-in existing admin account, open each main section and
return to Dashboard. Check that loading finishes, content or an honest empty
state appears, and no visible error/blank screen occurs:

| Screen | Rehearsal status |
| --- | --- |
| Dashboard/sign-in | User-confirmed loaded |
| User management | User-confirmed loaded |
| Students | User-confirmed loaded |
| Results | User-confirmed loaded; detailed content/action verification remains separate |
| Progress | User-confirmed loaded; detailed history/action verification remains separate |
| Settings | User-confirmed loaded; no password change requested |
| Audit logs | User-confirmed loaded |

Use fictional demonstration records or an appropriately authorized presentation
dataset. Do not include identifiable student names, handwriting or sensitive
record details in shared reports/screenshots. Browsing a screen does not verify
its save/delete actions; no edits are needed for this read-only rehearsal.

Latest manual report: user said all requested admin pages load. This establishes
user-reported navigation success, not independent visual inspection or complete
result/history/action coverage. Next rehearse the user app at
`http://127.0.0.1:5174/` with existing teacher, expert and parent demo accounts.
Teacher update: user confirmed the teacher dashboard, student list, results list
and existing result work. This is user-reported navigation/detail evidence;
upload/inference/write actions remain separate. Next is expert dashboard/results
and an existing review view without submitting changes, then parent released
results. Use the
current Vue/MySQL accounts rather than the fictional Supabase Auth account.
Do not upload a real child's handwriting or alter a validation just for rehearsal.

Expert update: user confirmed dashboard, result list and an existing review view
with handwriting image/details work. Validation submission was not tested.
Next check parent dashboard and released-result list/detail for a linked student.
An empty reviewed-results state can be correct if no linked Validated result is
available; do not change validation or ownership to populate the demonstration.

Parent update: user reported it works. Populated reviewed-result availability was
not separately specified; record view success without claiming a new release or
full record/image coverage. All four existing role screen walkthroughs are now
user-reported working. Fresh upload/inference and expert submission remain separate.

Guest preparation: corrected two dashboard cards to `/guest/demo`, matching the
router; the user-app build passed. Next use the existing guest demo account and a
synthetic handwriting sample to run Demo Screening. This is not an official
student result; source does write a guest audit event and removes the temporary
uploaded file. The fresh inference/navigation check remains pending. A single
demo image confirms execution, not model accuracy or diagnostic validity.

## Suggested five-minute speaking order

1. **Purpose:** GraphiScan supports handwriting screening and expert review.
   It is a screening aid, not a clinical diagnosis.
2. **Existing prototype:** Show the dashboard and a permitted student/result/
   progress example. Identify this as the current Vue/MySQL system.
3. **Classification:** The active predictor is binary: Normal / High Potential.
   Model output scores are not clinical probability. Do not demonstrate a new
   three-class model or model selector as completed.
4. **Hosted progress:** Summarize verified Supabase connection, session/password
   change and temporary fictional-notice acceptance results. These are standalone
   hosted backend checks, not completed Vue/Expo client integration. The local
   test totals are 118 Python, 466 contract and 151 isolated SQL checks; hosted
   Auth/password/privacy reports passed 11/12/9 checks respectively.
5. **Remaining work:** Shared resource APIs and private data migration/storage,
   model comparison/integration, Expo Android, remaining access/recovery tests,
   hosting/release and manuscript/slides. Temporary notice applies to fictional
   testing only; real-use wording and institutional inputs remain open.

If a live screen fails, state the failure accurately and use the verified
progress summary. Do not silently describe a planned feature as running.
Keep the local services running and avoid last-minute resets/migrations.
