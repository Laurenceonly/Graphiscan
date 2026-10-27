# GraphiScan reference-led rebuild - 2026-10-26

Current implementation follows the user's reference study, free-imagery permission
and subsequent steering. It is locally reviewable, not user-approved or deployed.

## Direction and compositions

The opening is a full-viewport, licensed photograph of handwriting. The user
explicitly requested retaining this first section after white was mistakenly
applied there; it is restored. White applies to Platform, Understanding Dysgraphia,
Who It's For, FAQ, download close and the dedicated download page. Typography is
self-hosted Manrope, dark navy and the existing GraphiScan steel blue.

The photograph is Khoiru Abdan's Write Your Story, under the Unsplash License.
Three candidates were downloaded and inspected. The selected frame keeps the
hand/pen on the right and a useful writing surface/quiet area for the headline.
The original adult stock subject is not represented as a learner with dysgraphia.
No reference-site imagery was copied and no paid or generated media was used.

The product composition pairs the actual admin dashboard in a laptop with an
actual Expo screen in a foreground phone. Fictional records are captioned.
Workflow choices update the mobile preview and a nearby explanation. Role tabs
provide separate permissions/capabilities, with a phone for mobile roles and a
laptop for the admin. All phone bodies have one graphite color around a distinct
white display; the earlier white-top/black-side enclosure was corrected.

Section padding uses a shared responsive scale. Desktop Platform groups the
device composition beside the workflow so its important content appears together.
Educational and role layouts are similarly more compact. Long phone content
scrolls naturally; nothing is cropped merely to force every section to 100svh.
An optional spacing-preference question was sent but no answer was assumed.

The download page is a separate white release presentation with a phone mockup,
one release area, a real unavailable state and four short installation steps.
The source contains no fictional APK URL. A configured release state is tested
with an intercepted example.invalid fixture without an actual download.

## Motion and useful interaction

| Scene | Motion and settled state |
| --- | --- |
| Opening | Photo settles from scale1.06 to1 over2.1s; principal heading enters as two lines over1.15s with0.1s stagger. Photo and type travel together through natural hero exit, with separate portrait amplitudes. Controls remain ordinary links. |
| Product | Laptop and phone move into place at different rates as the composition enters, then hold for reading. The screen/copy changes briefly bridge pointer selection; keyboard tab changes are immediate. |
| Educational trace | Three.js draws an original lowercase a as a metal-tipped pen follows its curve. GSAP drives2.8s trace progress, then a short pen lift. Replay and optional baseline guides are functional. |
| Reduced motion / failure | Opening/product movement is omitted. Trace shows its complete state. Context loss reveals the SVG letter and disables unusable controls. |

The trace chunk loads only near the educational section. Rendering stops offscreen
and in hidden tabs; resources are disposed on page exit/HMR. No locked pointer,
scroll hijacking, background particle decoration or public inference is used.

## Completed review evidence

Production build and strict TypeScript pass. Vite retains its size advisory for
the lazy Three.js chunk (about551KB minified/138KB gzip); it is not first-paint JS.
The shared entry is about8.35KB and GSAP is independently loaded for the home page.

Five viewport checks passed at1440x900,1920x1080,768x1024,390x844 and320x667:
no horizontal overflow, full-height opening, white surfaces, no diagonal arrows,
native Discover text underline, device-frame structure/color, all role/workflow
selections, role-specific laptop/phone state, responsive arrow-key tabs, FAQ and
mobile menu/Escape behavior. Captures: output/playwright/landing-white-*.png.

Actual trace progress advanced from0.095 to0.286 in the sampled interval. Guide
state, replay, reduced-motion still/replay and a deliberate WebGL context-loss
fallback passed. Three information routes and both unavailable/configured release
states passed. Zero page errors and no actual APK download or protected API writes.

The later standalone download rebuild was independently checked at1440,390 and
320px, including release-state fixture, consistent phone enclosure and four steps.
All passed with zero page errors; its desktop/phone full-page captures were read.
The product caption was moved out of the laptop screen after visual inspection.

Read desktop/phone opening, product, role/admin, trace and download captures.
The supplied generic checker is rerun against the final built output; its result
must be distinguished from custom behavior checks and human design acceptance.

Final supplied-checker result: four pages and their internal links checked,
with no remaining font/missing-file/console/touch-target findings. It still
exits1 for two intentional shared-image heuristics: the official logo across
pages and the actual teacher interface reused in product/download previews.
Those are reviewed design choices. The checker was not modified and no blanket
green result is claimed. Its phone-top and download captures were inspected.
It does not produce its engine-specific hero contact sheet for this GSAP scene;
the custom desktop/phone captures supply that visual evidence instead.

The first production check exposed that its static server rejects TTF assets.
The build contained the TTF, but delivery now uses a self-hosted Latin WOFF2
variable subset (about25KB versus165KB), with the same font license. Rebuild
and checker rerun confirm successful font delivery. Evidence is in
output/playwright/10k-landing-rebuild-woff2/.

## Critical design self-review

Compared a separate text-heavy workflow below a very large product image with
the current composition that puts a compact workflow beside the devices. Selected
the latter to answer the user's spacing/visibility feedback. Phone reflows the
same content in reading order. A uniform graphite frame replaces the inconsistent
white/black top trim identified by the user.

Retrospective self-review scores, not user ratings or certifications:

| Outcome | Earlier rejected pass | Current pass | Evidence / limit |
| --- | ---: | ---: | --- |
| Point of view |4|7| Writing photograph, original trace and authentic app content |
| Typography |5|7| Local Manrope, fewer levels, consistent spacing |
| Color |5|7| Preserved photographic opening; requested white content surfaces |
| Hierarchy |4|7| Compact product/workflow and one clear download release area |
| Imagery |4|7| Licensed subject photograph and consistent hardware mockups |
| Motion |4|7| Coordinated scroll/product behavior and tested pen trace |
| Mobile |5|7| Five responsive sizes, including short/narrow phone; no physical device |
| Polish |4|7| Tested controls and failure states; visual approval still outstanding |

Remaining: user's visual review, physical-phone/performance check, signed APK and
minimum-device information, real download/install verification, final public URL
and QR, approved public team/contact/legal content, and authorized publication.
