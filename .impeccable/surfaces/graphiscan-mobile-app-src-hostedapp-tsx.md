---
version: 1
slug: "graphiscan-mobile-app-src-hostedapp-tsx"
primary_target: "graphiscan/mobile-app/src/HostedApp.tsx"
related_targets: ["graphiscan/mobile-app/src/ui.tsx","graphiscan/mobile-app/src/SignInPanel.tsx","graphiscan/mobile-app/src/AccountSetup.tsx","graphiscan/mobile-app/App.tsx"]
---

# GraphiScan native workspace

Palette update2026-10-25: user selected steel blue #355c8c branding/logo, muted
blue #45638a controls and neutral slate surfaces matching the revised admin.
Use #aac0dd for dark interactive text and Scan lettering. This supersedes the
earlier royal-blue pin below; retain native layout and server behavior.
Latest logo choice: user supplied Glossy Interlocking Blue G-S Logo.png for both
apps. Render its original glossy blues directly, without recoloring filters.

Scope: Expo login, onboarding, role Home, students, results/history, details and profile.
Mode: Operate. Android phone first. Browser is a development preview only.
User instruction: build directly in Expo, no mockup-first round. Retain name,
supplied logo, blue identity, three roles, concise copy and server behavior.

## Direction contract

THESIS: A student-record workspace that makes the next role task and the evidence
already recorded obvious; replace the anonymous stack of equal buttons and counts.

OWN-WORLD: GraphiScan blue for the primary task and selection, ink for names,
cool paper surfaces, Material/Roboto type roles, restrained state chips and flat
record rows. No invented progress charts, illustration, slogans or medical claims.

STORY: A teacher starts screening, an expert opens assigned reviews, and a parent
opens released reports. Recent records connect those actions to actual students.

FIRST VIEWPORT: Branded native app bar, a name/role row, one compact primary action,
supporting navigation rows, and recent work with separately labelled model and
expert-review state. Fixed native navigation anchors the bottom. Login uses one
vertically balanced white layout led by the supplied logo/wordmark, a concise
sign-in heading and tinted fields with a steel blue action. Shared spacing continues
into details. User reconfirmed clean, professional white/blue, requested stronger
hierarchy, then rejected the large blue-header/curved-form draft. Final proposed
login follows the full search comparison; it awaits user visual feedback.

FORM: Children's learning-record portfolio, candidate6 of the grounded list,
translated into standard Android navigation/controls rather than paper decoration.
Signature interaction: selecting a recent record opens its model/review handoff
without an intermediate dashboard. seed:d598b2ae8890d42f.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

Evidence update2026-10-23: GraphiScan_Pixel_6 API36 emulator is available and
native login rendered in light/dark through Expo Go58.0.5. Other native role
captures and full review remain open. Browser layouts are engineering previews,
separate from Android runtime approval and physical-device evidence.
Existing logo is the only shipping raster; no new imagery is needed.

Login reference selected after visually comparing all48 cards visible at the user's
https://dribbble.com/search/mobile-ui-login:
https://dribbble.com/shots/8759887-Mobile-app-Login-Signup-UI-concept
Use its logo-led white layout and spacing as inspiration. Interface branding uses
the user-selected steel blue #355c8c. No reference artwork or
unsupported authentication controls are shipped. Earlier blue-header drafts are
rejected and are not a reusable design pattern.

Overall UI reference inspected: https://dribbble.com/shots/19280594-Storage-Mobile-UI
Retain its flat record rows and clear spacing within GraphiScan's white/blue identity.
Loading uses pale-blue row skeletons during initial requests, a 1400ms opacity
pulse, and static placeholders for reduced motion/background/unfocused state.
Existing records stay visible during refresh. No minimum artificial wait is added.

Continuation2026-10-24: Students/Children now fill the loading viewport for every
hosted role; legacy Students/progress also opt in. Student and screening rows keep
their respective densities. Shared search fields use a decorative20-unit Material
icon and a name-search placeholder with an accessible label and focused frame.
Four fictional browser cases verified roles, size/theme/motion, search/Enter/clear
and request outcomes. Native hosted-student light/dark-font1.3 loading captures
passed; separate native search-field capture is not claimed verified.

Results refinement2026-10-24: screening placeholders now continue through the
measured list height, avoiding the former two-row block and large blank area.
Five fictional browser role/height/theme/motion cases passed, together with
loaded/empty/error/refresh checks. Native loading-only light and dark/font1.3
captures fill the content area while keeping navigation visible. Source remains
local; actual model submission and the full role workflow are still unverified.

Defense minutes checked: keep issued accounts/password/privacy gates, readable
recorded classifications, attributed expert notes, server Initial/Follow-up labels,
and server-provided model selection. Grade appears in student rows. Native school
and grade filters and teacher student create/edit are now implemented in source.
The final 2026-10-23 fictional browser matrix passed, including the dark picker
surface. Real model inference and hosted/device workflow verification remain gaps;
the browser review does not establish their completion.
