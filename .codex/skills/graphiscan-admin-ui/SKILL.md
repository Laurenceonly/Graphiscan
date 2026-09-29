---
name: graphiscan-admin-ui
description: Make or review a bounded visual change in GraphiScan's Vue admin interface while preserving navigation and page behavior.
---

# GraphiScan admin UI

Use this skill for a requested visual change in `graphiscan/admin-web/`.

1. Read `AGENTS.md` and the relevant portion of `KNOWLEDGE.md`. Locate the rendered Vue component and every CSS rule that can affect the target, including responsive rules.
2. State the requested visual outcome and the smallest set of files and selectors that control it. Preserve links, routes, authentication, data requests, and unrelated page content unless the user explicitly asks to change them.
3. Make the visual change. Check text, icons, hover, active states, and the narrow layout when the edited selectors affect them.
4. Run `npm.cmd run build` from `graphiscan/admin-web/`. Inspect the UI when a browser is available, and review `git diff` for unrelated edits.
5. Report what changed and what was actually verified. Do not claim a navigation flow was tested if only the build passed.

For a sidebar change, inspect `src/layouts/AdminLayout.vue` and the `.sidebar`, `.nav-link`, `.nav-icon`, and responsive rules in `src/style.css`.
