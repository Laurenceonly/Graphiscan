# GraphiScan public website

Standalone Vite + TypeScript multi-page website. Existing admin, Expo, API and
database applications are unchanged. No protected API requests or analytics.

## Local use

From this directory, run `npm.cmd install`, `npm.cmd run dev`, then visit
http://127.0.0.1:5180. `npm.cmd run build` runs strict TypeScript and produces
`dist/`; `npm.cmd run preview` serves the production build on the same port.
Use `npm` on platforms without Windows's npm.ps1 execution-policy restriction.

## Structure

- index.html: photographic opening, web/mobile product composition, workflow,
  sourced dysgraphia information, role explorer, native FAQ and compact footer.
- download/, about/, privacy/: independent direct-entry HTML routes.
- src/style.css: centralized palette, type/spacing rules, responsive layouts.
  The full-screen photographic opening is preserved; subsequent sections use
  white surfaces and a shared spacing scale. Device chrome is presentation only.
- src/main.ts: keyboard-accessible workflow/role tabs, mobile menu and release
  configuration. No input is analyzed or sent to a backend.
- src/motion.ts: GSAP/ScrollTrigger opening and product choreography, responsive
  and reduced-motion behavior.
- src/stroke-scene.ts: unused previous letter demonstration, no longer imported
  or included in the production bundle.
- src/config.ts: public URL validation; only credential-free HTTPS links allowed.
- public/images/: existing branding and fictional UI previews; provenance beside them.
- public/fonts/: self-hosted Manrope variable font and its SIL OFL license.
- Root .10k/REBUILD.md and .10k/reference-study.md: current design decisions.

Without JavaScript, the story, initial role/workflow and native FAQ remain readable.
Interactive tabs and release configuration require JavaScript.
Motion respects prefers-reduced-motion; there is no pinned or hijacked scrolling.
Box groups use reversible750ms scroll fades and450ms CSS hover/overlay feedback;
role/workflow details fade over500ms and real presses respond in160ms.
Hero/heading entrances replay on every scroll revisit. Top navigation uses a
simple text underline and hash-based selected-section state.
The first hero entrance is CSS-led to avoid late-module flashing. GSAP initializes
after fonts/page layout, leaves initially visible content settled and replays
later visits. Reload preserves browser-restored scroll position. Platform devices
fade as one stable stage; the role reading column fades as a group. Headings no
longer translate, and reduced motion clears animation styles.
Hover movement is limited to fine pointers and removed under reduced motion;
reduced motion keeps all content fully visible.
Home/download footers use one row with copyright text and navigation, without a logo. The homepage photograph
is credited on About; provenance is recorded in public/images/README.md.
The photo loads first; the removed letter demonstration no longer loads WebGL.
Admin previews use a laptop enclosure; mobile previews use a continuous graphite
phone body with a separate display. The admin role changes that preview to the
laptop treatment. These are generic hardware mockups, not an iOS release claim.

## Configuration and APK updates

The dedicated download route uses the same phone frame and white layout, with
one release area and four installation steps. Missing APK configuration disables
the download control; the configured state exposes the supplied URL and metadata.

Copy `.env.example` to ignored `.env.local` and set only public values:

| Variable | Meaning |
| --- | --- |
| VITE_APK_URL | Direct, stable HTTPS signed APK release URL; blank keeps Coming soon |
| VITE_APP_VERSION | Optional actual release version |
| VITE_APK_SIZE | Optional human-readable file size |
| VITE_RELEASE_DATE | Optional actual release date |
| VITE_ADMIN_URL | Existing public HTTPS admin sign-in URL; blank hides link |
| VITE_SITE_URL | Final public HTTPS website origin; blank omits canonical metadata |

Publish a signed APK to the chosen release host, verify its checksum/signing,
download and install on supported devices, then set the public URL and metadata
and rebuild. The site does not build/sign an APK or verify remote artifacts.
Both cross-origin download and Android installation must be checked when supplied.
The homepage routes to /download/ even when no release exists. It never links to
`#` or a fabricated APK. Update the download copy and required Android version
with the release. QR generation is deferred until a public website URL is known.

## Vercel

Create a separate Vercel project with Root Directory `graphiscan/landing-web`,
framework Vite, build `npm run build`, output `dist`. Add the public environment
variables in that project, then rebuild when changing them. This is a multi-page
site; do not add an SPA catch-all that swallows /download/, /about/ or /privacy/.
The included vercel.json applies basic response headers and clean URLs. No other
application's deployment configuration is changed. Deployment is not performed.
Supply the final domain before adding canonical URLs, sitemap or a download QR.

## Content boundaries

Current source uses binary Normal / High Potential screening, separate from
expert Validated / Flagged review. No accuracy, clinical approval, successful
real-use workflow or model calibration is claimed. Public medical background
links to NIH and MedlinePlus; product claims are derived from current app/API source.

Still requires APK, device checks, public URL/QR, public team/contact details,
approved legal/privacy content, final content approval and deployment. This is
the initial website, not a declaration that those project release gates passed.
