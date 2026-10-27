# GraphiScan reference study - 2026-10-26

User supplied Linear, Apple, Samsung Philippines and Igloo after identifying
Lando Norris as a reference for craft. These are taste references, not source
assets or authorization to copy a site. No landing application code changed
during this study. The current GraphiScan treatment remains unapproved.

## Evidence

Visited the four exact supplied URLs in a real Chromium browser at 1440x900 and
390x844. Captured initial, later, pointer-position and early-scroll views in
ignored output/playwright/reference-*.png. Inspected settled Linear, Apple and
Samsung views, and Igloo after a second longer load. Igloo initially showed only
its loading screen; later desktop/scroll captures and a resized loaded phone
view showed the actual scene. These are sampled browser observations, not an
exhaustive audit or physical-device verification. Temporal differences alone
do not prove that pointer movement caused an animation.

Primary reference URLs:
- https://linear.app/
- https://www.apple.com/
- https://www.samsung.com/ph/
- https://www.igloo.inc/
- https://landonorris.com/

Earlier creator-authored Lando research:
- https://tympanus.net/codrops/2025/12/05/from-illusions-to-optimization-the-creative-webgl-worlds-of-adrian-gubrica/
- https://tympanus.net/codrops/2026/08/17/creativity-at-enterprise-scale-without-compromise-the-offbrand-story/

Igloo's live scene was observed directly. A creator case-study URL was found but
the web reader timed out; do not describe its implementation from an unread
article or treat third-party technical breakdowns as primary verification.
document.querySelectorAll('canvas') returned zero despite the rendered 3D scene;
that selector result does not establish the absence of WebGL.

## What each reference contributes

| Reference | Observed design characteristic | Application to GraphiScan |
| --- | --- | --- |
| Linear | Compact navigation; left-aligned, concise product statement; a large detailed interface; restrained dark tones; an opening that settles into legible content | Build a clear information hierarchy and make actual GraphiScan interfaces large enough to read. Settle motion before asking the visitor to study a screen. |
| Apple | Short product headings and a small set of actions; generous negative space; large, deliberately framed product imagery; light/dark scene changes; distinct portrait image composition | Give each scene one subject and keep its surrounding explanation brief. Recompose mobile scenes and preserve readable holds. |
| Samsung Philippines | Broad, nearly edge-to-edge moving product imagery; sparse overlaid copy; clear category navigation; product arrangement adapted to portrait | Treat the screen as a composed visual stage rather than filling it with repeated text boxes. Put navigation and action outside the visual's action area. |
| Igloo | A full-viewport environment with consistent ice materials, restrained blue-grey color and compact corner UI; the igloo changes and the camera viewpoint moves between observed states | Make the signature scene and surrounding layout belong to one material/lighting system. Use camera and object movement to carry a transition with a clear destination. |
| Lando Norris | A dominant subject; custom interactive face/helmet treatment; typography and small UI integrated into the overall composition | Invest in one specific, high-quality interaction and refine how the object, type, pointer and scroll respond together. |

## Interpretation, not an assumed user approval

The references span light, dark, software, consumer products and an immersive
3D environment. A dark background is therefore not the common preference.
The common qualities are deliberate hierarchy, an unmistakable focal point,
high-quality subject presentation, restrained copy and composed motion.

Proposed GraphiScan direction: product clarity from Linear and Apple, spatial
scale from Samsung, and one subject-specific interaction with the cohesion of
Igloo/Lando. Keep GraphiScan's own steel blue identity, actual supported features
and screening-versus-diagnosis language. Build one coherent design rather than
assembling visible fragments from five brands.

## Corrections to the previous attempts

- A flat or simply folded paper mesh beside large type is not enough to create
  an art-directed scene. Its geometry, material, light, shadow, framing and
  relation to the interface need a clear purpose.
- Filling 100svh is a layout constraint, not proof of quality. The subject must
  have sufficient visual detail and scale to justify the space.
- Rewriting headlines and changing colors repeatedly did not resolve the weak
  composition. Resolve the opening and a representative product scene together.
- Repeated phone previews and repeated section structures dilute the visual
  story. Use one readable product demonstration, then change the layout's job.
- No arbitrary particles, orbit rings, glowing accents, invented data or
  decorative counters. No generic claims or excessive captions.
- Keep navigation and primary actions stable. Use Three.js for actual spatial
  behavior and GSAP to coordinate it; avoid unrelated entrance effects.

## Next design work

Before another broad implementation rewrite, compose the opening's settled
frame and one lower product scene at desktop and phone sizes. Define the entry,
transition and reading hold, with an explicit role for each moving element.
Use the real app with fictional records and a deliberately created handwriting
illustration; no real learner data or invented prediction. The eventual APK
can still be added through the existing unavailable-release state.

Study complete; application unchanged. No new design acceptance, runtime pass,
deployment, paid-media allowance or model change is implied by these notes.
