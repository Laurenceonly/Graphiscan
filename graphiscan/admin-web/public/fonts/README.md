# Admin font asset

Inter variable, normal style, weights 100–900. Downloaded 2026-11-05 from the
official Inter project:
https://github.com/rsms/inter/blob/master/docs/font-files/InterVariable.woff2

SHA-256: `693b77d4f32ee9b8bfc995589b5fad5e99adf2832738661f5402f9978429a8e3`

The accompanying `Inter-LICENSE.txt` is the project's SIL Open Font License.
Vite copies these public assets into the production bundle. The admin preloads
this local font and waits for actual loaded font faces before revealing the app.
If loading exceeds the startup timeout, that document keeps its system fallback
font to avoid a later text-width jump. It no longer requests Google Fonts.
