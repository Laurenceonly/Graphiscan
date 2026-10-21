# Admin sign-in preview

`graphiscan-logo.png` is the user's supplied PNG logo, copied without altering
the artwork from the extensionless `logo gs` file on 2026-10-21. It is displayed
beside the login wordmark in the upper-left of the admin sign-in shell.
Its original whitespace/background is kept.
The admin view applies a white-preserving SVG color filter at render time to
match the primary blue palette; the supplied PNG itself is not recolored.

`admin-workspace-preview.png` is a1440x1000 local Chromium capture of the current
hosted Vue dashboard with intercepted fictional API responses: three screenings,
two synthetic student names and one synthetic school. It contains no real
accounts, students, handwriting images or hosted records. It is a decorative
product preview, not a live dashboard or evidence of populated hosted verification.

Updated during the2026-10-21 reference-based admin visual checks, from the ignored
`output/playwright/hosted-dashboard-preview.png` produced by
`tools/check_hosted_dashboard_browser.js`. Displayed inside the CSS preview frame
in `AdminLoginPanel.vue`; do not replace it with private data.
