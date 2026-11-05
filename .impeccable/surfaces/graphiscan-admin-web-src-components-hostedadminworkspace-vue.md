---
version: 1
slug: graphiscan-admin-web-src-components-hostedadminworkspace-vue
primary_target: graphiscan/admin-web/src/components/HostedAdminWorkspace.vue
related_targets: [graphiscan/admin-web/src/styles/workspace-viewport.css, graphiscan/admin-web/src/style.css, graphiscan/admin-web/src/components/HostedAdminRecords.vue, graphiscan/shared/HostedDirectory.vue, graphiscan/admin-web/src/components/HostedSchoolPeople.vue, graphiscan/admin-web/src/components/HostedStudentDetails.vue]
---

# GraphiScan admin workspace

Mode: Operate. This is the Vue web administration surface, separate from the
native Android brief. Preserve server authorization, data scope, routes and editors.

2026-11-04 user direction: use the third supplied dashboard reference (Mondays)
for a white workspace with restrained borders, aligned content, clear hierarchy
and consistent controls. Keep GraphiScan's supplied logo, Inter and muted blue
identity. No unsupported search, notifications or decorative data.

Keep the page fixed to the viewport; scroll records within the appropriate panel.
The activity chart itself must fit without scrolling. Use one frame per group,
a divided summary row, thin table separators and a solid blue selected nav item.
Keep matching controls the same size across pages, including search icon artwork.
Do not add redundant account-name/Administrator labels to the header.

Schools uses a table with no grade badge or separate cards. Row actions are View and Edit; View opens
the existing school/grade roster. The school heading, equal-size actions and grade
tabs stay above the scrolling roster area. Preserve per-school/grade requests,
revisions, paging, candidate eligibility and permission-dependent name resolution.

Student View opens a workspace subpage with record details and scoped screening
history, with explicit Edit and a contextual Back action, no extra sidebar entry.
Use vertical column dividers in record/details groups and horizontal ones in
stacked phone records. Screening titles use their recorded Initial/Follow-up type;
Reviewed by uses actual authorship. The manual screening assignment form is removed;
admin school/grade assignment is the agreed expert responsibility policy. Prepared
migration025 grants the complete scope and removes the per-screening ownership
prerequisite; hosted rollout remains pending. Historical authorship stays unchanged.

Progress now plots stored screening labels across complete authorized history,
oldest first, using StudentScreeningChart.vue. Keep Initial/Follow-up metadata,
keyboard/touch point selection. Keep the chart and search fixed; only the student
list scrolls. Use a stable chart frame through student changes, loading and errors. The action is View progress. Never plot confidence as severity or
claim clinical improvement; one screening stays one point and unknown labels
remain explicit.

Visual review uses intercepted fictional records only. Local implementation and
browser evidence are not publication or approval of the final composition.
