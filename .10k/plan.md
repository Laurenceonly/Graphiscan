# GraphiScan landing website - current checkpoint

## Authorized scope

The user requested a reference-led rebuild of the initial site, with Three.js,
GSAP, full-screen responsive presentation and freely usable internet imagery.
Reference study: reference-study.md. Current visual brief: REBUILD.md.
Source: graphiscan/landing-web. Static deployable output: its dist directory.
Local preview: http://127.0.0.1:5180/. No publication or Git commit requested.

Production scope is local code and owned/free assets. No paid media, model
switch, purchases, generated imagery, provider credits or hosting changes.
The supplied 10k-websites skill is extracted at
.local-tools/10k-skill/10k-websites; tools copied unchanged to .10k/tools.
Its design/review guidance is applied within the explicit Three.js/GSAP scope.

## Current implementation

- Superseding clarification: restored the earlier white control/FAQ styling and
  branded home/download footer with nav and a bottom information row. User also
  requested section separation; subtle blue-tinted boundaries now divide white
  homepage sections and footer. Photo hero and corrected devices retained.
  Build and1440/390/320 home/download browser checks pass; visual approval pending.
  The compact logo-free footer decision below is historical.

- Latest decision: restore the pre-experiment white presentation, with navy
  headings, muted copy, blue controls and compact footers. Removed later all-blue
  typography and enlarged footer/Back to top. Preserve the photographic opening,
  device mockups and reduced-motion scroll fix. Latest build/typecheck and
  home/download browser checks at1440/390 pass with no overflow or page errors.
  User visual approval is still pending.

- Latest cleanup: no repeated footer logo/wordmark, decorative section rules or
  redundant eyebrows. Footer is navigation plus the small photo credit where
  applicable. Download copy uses one Coming soon state and shorter installation
  steps. Preserve the header logo and photographic opening. Build/typecheck and
  1440/390 home/download checks pass with no page errors or horizontal overflow.

- Retain the full-screen photographic opening. The user rejected replacing it
  with white; white applies to the sections below it.
- No diagonal arrows. Discover GraphiScan uses a close native text underline.
- Platform/Understanding/Who It's For/FAQ/download use white surfaces and a
  shared responsive spacing scale. Main compositions are compact; long mobile
  content can scroll rather than being cropped into a fixed-height box.
- Real fictional admin/mobile interface previews are in laptop/phone mockups.
  Phone enclosure is uniform graphite with a separate white display. Admin role
  changes the role preview to the laptop treatment.
- GSAP opening/type/product motion; lazy Three.js letter/pen trace with replay,
  guides, reduced-motion still and context-loss SVG fallback.
- Download page rebuilt after user feedback: one white release area, phone
  preview and four installation steps. Missing APK remains Coming soon.
- Self-hosted Manrope WOFF2/SIL OFL and licensed Khoiru Abdan/Unsplash photograph;
  provenance is in public/images/README.md and public/fonts/OFL.txt.

## Verification

Current strict TypeScript and production build pass. Near-section Three.js chunk
retains a size advisory. Five viewport home/role/workflow/keyboard/menu checks,
trace replay/guides/progress, reduced motion, context-loss fallback, three routes
and unavailable/configured release fixtures pass with zero page errors. The later
download rebuild passes1440/390/320 checks. Captures were visually inspected.

The supplied checker first rejected TTF because its static server only permits
WOFF/WOFF2 fonts; changed to a25KB WOFF2 delivery file and rebuilt. Final checker
result is recorded in design-package.md. Intentional shared branding/interface
reuse is separately reviewed rather than replacing authentic images to satisfy
a generic no-duplicate-image heuristic.

## Next

User visual review remains open. No claim of physical-device, actual APK install,
live screening workflow, public deployment or approved legal/privacy release.
Later supply signed APK/minimum Android support, public domain/QR and reviewed
public team/contact/legal details. Earlier core app workflow remains deferred;
root RESUME.md preserves its existing Initial Screening checkpoint.
