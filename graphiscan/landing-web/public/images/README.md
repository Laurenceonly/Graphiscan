# Public preview provenance

## Reference-led rebuild assets

`handwriting-hero.webp`: photograph by Khoiru Abdan, “Write Your Story”,
https://unsplash.com/photos/a-person-writing-on-a-piece-of-paper-with-a-pen-TKk29MxSjAA
Published 2023-06-19. Source page explicitly marked Free to use under the
Unsplash License, checked 2026-10-26: https://unsplash.com/license.
Downloaded through Unsplash's image CDN as a 2000px-request WebP. The actual
delivered image is 1759x1408. Crop/position is applied in CSS for each viewport.
This is stock illustration of writing, not a GraphiScan learner or evidence of
a writing condition. Photographer credit appears on the About page.

`graphiscan-mark.webp`: 256px delivery derivative of the existing transparent
glossy mark, optimized using Sharp (quality95); no recoloring or redrawing.
The original copied PNG remains available for provenance. The app logos and
other project assets are unchanged.

No reference-site images or generated media are incorporated. The 3D lowercase
letter, paper and pen are original code geometry in src/stroke-scene.ts.

The self-hosted Manrope variable font is from google/fonts/ofl/manrope, under
SIL Open Font License 1.1; the license is supplied in public/fonts/OFL.txt.
Delivery uses the Latin WOFF2 variable subset from Google's font CDN:
https://fonts.gstatic.com/s/manrope/v20/xn7gYHE41ni1AdIRggexSg.woff2
The original TTF is archived only in ignored local tooling. WOFF2 is about25KB
and is supported by both Vite/Vercel and the supplied static review server.

## Existing application previews

- graphiscan-mark.png: existing transparent derivative of the user's supplied
  glossy GraphiScan logo, copied from admin-web/public/graphiscan-favicon-cutout.png.
- admin-workspace.png: existing admin-web/src/assets/admin-workspace-preview.png;
  actual Vue interface rendered with intercepted fictional dashboard records.
  The capture predates the later static Admin Workspace header.
- teacher-home.png, parent-home.png, expert-home.png: existing 2026-10-25 Expo web
  captures from output/playwright/expo-glossy-theme-{role}-390-light-home.png.
  These show actual components with explicitly fictional role/learner records.

Screenshots are illustrative, not evidence of full hosted role verification,
device approval or clinical performance. No real learner handwriting is included.
The ruled-paper handwriting graphics are original code-native SVG/CSS illustrations.
