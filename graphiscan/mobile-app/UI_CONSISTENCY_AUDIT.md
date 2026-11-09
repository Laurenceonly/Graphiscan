Latest implementation follow-up (2026-11-09): user rejected the collapsed shared-filter trial. QuickFilters.tsx now supplies visible status buttons for teacher Results/expert Reviews and visible grade buttons for teacher Students. Parent Children retains advanced filters. The inventory and recommendations below describe the earlier audit snapshot; collapsed-filter unification is superseded. New teacher native acceptance remains pending.

# Mobile UI consistency review — 9 November 2026

## Scope and evidence

Reviewed every current hosted mobile screen used by teachers, experts and parents,
including sign-in, onboarding and shared recovery states. Sources are under
`src/HostedApp.tsx` and its imported components. Legacy-mode screens, Vue admin
and the retained Vue user app are separate surfaces and excluded.

This audit is read-only on application code. The separately requested expert
navigation and Reviews filters were completed before this review.

Native evidence this session: teacher Home, Students, Student details, result and
Profile; expert Home, result/review form and Reviews. Expert All/Pending displayed
the existing pending record; Flagged/Validated displayed their correct empty
messages. No review was saved. Parent screens and onboarding were inspected in
source, not through a newly authenticated native session. Error, large-font,
TalkBack, tablet and physical-device behavior were not exhaustively exercised.

## Verdict

The app already shares one useful foundation: MaterialIcons, white surfaces,
steel-blue actions, native navigation, common fields and 52-unit shared buttons.
The main drift is in action naming, icon meaning and review-status color mapping.
The two filter patterns can remain distinct because they solve different tasks:
an advanced directory form and immediate review-status selection.

## Role navigation

| Role | Current tabs | Student access |
|---|---|---|
| Teacher | Home · Students · Screen · Results · Profile | Directory plus Add/Edit student |
| Expert | Home · Reviews · Profile | Read-only student details/history from a screening |
| Parent | Home · Children · Reports · Profile | Linked-child directory/details; no editing |

These differences are intentional. The server continues to enforce scope and
report release. A matching visual system does not mean identical role permissions.

## Page-by-page inventory

| Screen | Roles | Current filters / selection | Current controls and layout |
|---|---|---|---|
| Sign in | All | None | Centered logo/form; brand-blue 56-unit button; visibility eye icon |
| Set password | All when required | None | Shared fields, visibility eyes, blue Save password and Sign out |
| Data Privacy Agreement | All when required | Acceptance switch | White reading flow, bold section titles, blue Agree and continue |
| Account unavailable / session restore | All | None | Shared notice, Retry or Check account access, Sign out |
| Home | All | None | Branded app bar, role action, recent record rows, View all, refresh text action |
| Students / Children | Teacher / parent | Filters button (`filter-list`); name, school, grade; Apply/Clear | Shared FlatList; teacher Add student (`add`); avatar/name/grade rows |
| Student / Child details | All via permitted route | None | Name then grade, school/age and guardian; View screening history; teacher Edit student |
| Add / Edit student | Teacher | Native grade/school selectors; exact parent lookup | Shared fields/selectors, blue Save student, outlined Cancel; draft protection |
| Screen handwriting | Teacher | Current-page student search; student/model radio rows | Choose/Replace image, Use camera, image remove (`close`), blue Submit for screening |
| Results | Teacher | No current list filter | Shared screening rows with separate Model/Review badges and date |
| Reviews | Expert | Immediate All/Pending/Flagged/Validated buttons | Same screening rows; selected status filter is blue; cursor resets on change |
| Reports | Parent | Released-only list; no status filter | Same screening rows; server returns currently Validated reports only |
| Screening history | All within scope | Show oldest/newest first | Shared screening rows and cursor paging |
| Screening result | All within scope | None | Model name, Result label/badge, scores; image reveal; report/history actions |
| Submit expert review | Expert, inside result | Validated green / Flagged red; follow-up switch | Remarks, optional recommendation, blue Save review; explicit uncertain-save recovery |
| Screening report | All within scope | None | Shared model section; saved expert author/status/notes/date; image reveal |
| Profile | All | None | Avatar (`photo-camera`), name/role, preloaded school names, Sign out (`logout`) |
| Sign-out / remove-image dialogs | Relevant roles | Confirmation only | Cancel outlined, confirmation currently blue; scrolling dialog, stacked actions for large fonts |

## Shared visual rules already in source

| Element | Current implementation |
|---|---|
| Main canvas | White, shared `Screen`, maximum content width 600, 20-unit content inset |
| Primary button | `#45638a`, white label, minimum height 52, radius 10, padding 12 × 18 |
| Secondary button | White, blue label, quiet 1-unit border; same shared dimensions |
| Authentication button | Intentional brand variant: `#355c8c`, minimum height 56, radius 12 |
| Fields / native selectors | Minimum height 52, radius 10, common labels; multiline minimum 110 |
| Body / section type | Body 15/23, section heading 18/26, detail name 26/34 |
| Icons | MaterialIcons throughout; search/visibility 20, button 22, destination/action 24 |
| Navigation rows | Shared chevron, flexible name column, grade beneath name; flat dividers |
| Feedback | Shared Notice and LoadingSkeleton; explicit empty/error content |
| Selection | Blue for filters and ordinary choices; semantic green/red for expert decisions |

## Findings, ordered by impact

### 1. P2 — Flagged has two semantic colors

Location: `src/ui.tsx:64`, `src/HostedScreeningActions.tsx:28`.
Category: Appearance / consistency.

The selected Flagged review button is red, while `Status` groups Flagged with
High Potential and renders the stored review badge amber. Users encounter two
colors for the same review status across form, Home, Reviews and report.

Recommendation: separate review-status color mapping from model classification.
Use red for Flagged review badges and green for Validated; retain the existing
model colors. A selected filter remains blue because it indicates the active
query, not a saved expert decision. Suggested action: `$impeccable colorize`.

### 2. P2 — The same destination uses different icons

Location: `src/HostedHome.tsx:15`, `src/HostedApp.tsx:134`.
Category: Platform conformance / consistency.

Teacher screening uses `edit` on Home but `upload-file` in the Screen tab. Expert
review uses `assignment-turned-in` on Home but `assignment` in Reviews. Parent
reports use `description` on Home but inherit `assignment` in the Reports tab.
All are MaterialIcons, but their meaning changes by entry point.

Recommendation: centralize destination metadata by role. Use the existing `edit`
for Screen, `assignment` for teacher Results, `assignment-turned-in` for expert
Reviews, and `description` for parent Reports at every entry point. Keep `home`,
`groups` and `person` for Home, Students/Children and Profile. Suggested action:
`$impeccable polish`.

### 3. P2 — History, retry and paging labels drift

Location: `src/HostedApp.tsx:106`, `src/HostedStudentDetails.tsx:32`,
`src/HostedStudents.tsx:41`, `src/HostedDirectoryControls.tsx:53`,
`src/HostedScreeningActions.tsx:101`.
Category: Copy / consistency.

The same history destination is called View student history and View screening
history. Read failures use Try again, Retry schools, Reload students and Reload
schools. Paging varies between More, Next page, Next students page and First page.

Recommendation: use View screening history; Retry [resource] for failed reads;
Refresh [resource] for voluntary fresh reads; Next page / First page for paged
lists. Retain precise wording for uncertain writes (Retry the same submission,
Reload current record), because those actions have distinct safety behavior.
Suggested action: `$impeccable clarify`.

### 4. P2 — Filter affordances lack a shared contract

Location: `src/HostedStudents.tsx:26`, `src/HostedApp.tsx:68`.
Category: Accessibility / consistency.

Directory filters are a collapsible form with an icon and Apply/Clear. Reviews
uses immediate selected buttons. Teacher Results has no filters. The directory
disclosure does not announce its expanded state. The review buttons announce
selection, but they are currently ordinary action-size buttons.

Recommendation: define two reusable variants: an outlined `filter-list` button
for advanced filters with expanded state and an applied-filter summary; a compact,
wrapping, labelled quick-filter group for review status. Keep quick status changes
immediate and server-filtered before pagination. Teacher Results can adopt review
status filtering if requested. Parent Reports should retain its released-only
meaning; Pending/Flagged filters would be misleading there. Suggested action:
`$impeccable harden`, then `$impeccable polish`.

### 5. P2 — Pending report follow-up looks like a completed decision

Location: `src/HostedApp.tsx:100`, `src/HostedScreeningActions.tsx:20`.
Category: Copy / truthful state.

An unreviewed report can show Follow-up needed: No because the stored flag starts
false. This presents a definitive value beside Not yet reviewed / Not recorded.

Recommendation: display Not yet determined while status is Pending; show Yes/No
after an expert review. Preserve the stored flag and server release logic.
Suggested action: `$impeccable clarify`.

### 6. P2 — Confirmation action colors do not distinguish removal

Location: `src/HostedScreeningActions.tsx:130`, `src/SignOutAction.tsx:35`.
Category: Appearance / action hierarchy.

Remove image and Sign out confirmations use the same blue primary button as Save.
The new opt-in danger button tone exists, but is only used for Flagged selection.

Recommendation: use the danger tone for the final Remove image action; adopt one
intentional sign-out confirmation treatment across all roles. Keep Cancel neutral
and leave ordinary navigation blue/outlined. Suggested action: `$impeccable colorize`.

### 7. P3 — Row chevrons and read actions use small style variations

Location: `src/WorkspaceUI.tsx:37`, `src/WorkspaceUI.tsx:45`,
`src/HostedHome.tsx:37`, `src/HostedApp.tsx:107`.
Category: Appearance / consistency.

Screening chevrons are 20 units; other navigation chevrons are 22. Home refresh is
an icon/text action while result refresh is a full outlined button. These are
minor presentation differences, with valid contextual uses.

Recommendation: centralize chevron size and define compact versus full-width
read-action variants. Use compact refresh in list contexts and a full-width
recovery action when it is the main available task. Suggested action:
`$impeccable polish`.

### 8. P3 — Design documentation has historical contradictions

Location: `DESIGN.md`, `.impeccable/design.json`.
Category: Documentation.

The current white-only direction overrides older dark-mode/cool-paper descriptions,
and the sidecar predates later source/document edits. Runtime uses the intended
white palette; this is documentation drift, not evidence of a broken dark theme.

Recommendation: refresh the sidecar and consolidate superseded descriptions in
a separately requested documentation pass. Suggested action: `$impeccable document`.

## Proposed shared action and icon vocabulary

| Purpose | Label / icon | Treatment |
|---|---|---|
| Advanced filtering | Filters · `filter-list` | Outlined disclosure; Apply blue, Clear outlined |
| Review quick filters | All / Pending / Flagged / Validated | Blue active selection; labels and selected accessibility state |
| Search field | `search` | One decorative leading icon; visible field label |
| Add student | Add student · `add` | Primary action on teacher directory |
| Choose image | Choose image · `image` | Secondary action; appears beside Use camera |
| Capture image | Use camera · `photo-camera` | Secondary action |
| Show / hide sample | View / Hide handwriting image | Secondary labelled action; save appears with preview |
| Save shown sample | Save handwriting image · `download` | Secondary action, visible only with preview |
| Open report | Open report · `description` | Secondary navigation action |
| Open history | View screening history · `history` | Shared wording; emphasis follows page task |
| Retry failed read | Retry [resource] · `refresh` | Secondary recovery action |
| Refresh current data | Refresh [resource] · `refresh` | Compact read action where appropriate |
| Sign out | Sign out · `logout` | Shared confirmation flow across roles |
| Open a record row | `chevron-right` | Same trailing size and position |

These are proposed mappings, not new implemented icons. Icons should identify a
task or destination; text-only Save/Cancel/status options remain clear and useful.

## Technical source audit appendix

Provisional source-based scores only, not runtime certification:

| Dimension | Score | Evidence / limit |
|---|---|---|
| Accessibility | 3/4 | Common labels/selected states, 48+ controls, reduced-motion handling; disclosure state and full TalkBack/scaling pass remain |
| Performance | 2/4 | Main directories use FlatList; upload choices are paged but map up to 100 rows; no frame/startup benchmark |
| Appearance / theming | 3/4 | Shared semantic palette, explicit white-only product direction; review color drift and local variants |
| Platform conformance | 3/4 | Native stacks/tabs/selectors/switches and one icon family; role destination icon mapping drifts |
| Adaptivity | 2/4 | Flexible rows and large-font dialog stacking; tablet/landscape/large-font full-role acceptance remains |
| Total | 13/20 | Acceptable under this rubric; device checks needed before a stronger rating |

No P0/P1 consistency defects were established in this bounded audit. Six P2 and
two P3 findings above are the prioritized cleanup list. Untested platform behavior
is recorded as a limit, not reported as a proven failure.

## Recommended order

1. `$impeccable clarify`: consistent action names and pending follow-up wording.
2. `$impeccable colorize`: separate model/review semantics and removal treatment.
3. `$impeccable harden`: shared filter selection/disclosure accessibility.
4. `$impeccable polish`: destination icons, row chevrons and reusable button variants.

Run these individually, together or in another order. Re-run `$impeccable audit`
after implementation and finish with `$impeccable polish`. No additional UI
cleanup from this audit has been applied.
