---
name: GraphiScan Android
description: Clean white and blue native student-record workspace for teachers, experts and parents.
colors:
  brand: "#095df1"
  brand-pressed: "#074bc2"
  on-brand: "#ffffff"
  brand-muted: "#eaf1ff"
  bg: "#f7faff"
  surface: "#ffffff"
  text: "#14263c"
  muted: "#5c6c81"
  border: "#dce5ef"
  primary: "#095df1"
  on-primary: "#ffffff"
  soft: "#e7efff"
  skeleton: "#d8e4f8"
  error: "#a72535"
  normal: "#176b3a"
  normal-surface: "#e7f4ec"
  high: "#895500"
  high-surface: "#fff2d9"
  bg-dark: "#101b2c"
  surface-dark: "#19283d"
  text-dark: "#f3f7fc"
  muted-dark: "#b5c5d8"
  border-dark: "#3c506a"
  primary-dark: "#9fc4ff"
  on-primary-dark: "#0d2447"
  soft-dark: "#213754"
  skeleton-dark: "#334a67"
  error-dark: "#ffb4b0"
  normal-dark: "#9bd8ac"
  normal-surface-dark: "#173f33"
  high-dark: "#f7cc83"
  high-surface-dark: "#49381e"
typography:
  title:
    fontSize: "26px"
    fontWeight: 600
    lineHeight: "34px"
    letterSpacing: "-0.5px"
  title-auth:
    fontSize: "22px"
    fontWeight: 600
    lineHeight: "30px"
    letterSpacing: "-0.3px"
  heading:
    fontSize: "18px"
    fontWeight: 600
    lineHeight: "26px"
  action-title:
    fontSize: "20px"
    fontWeight: 600
    lineHeight: "27px"
    letterSpacing: "-0.3px"
  home-title:
    fontSize: "22px"
    fontWeight: 600
    lineHeight: "30px"
    letterSpacing: "-0.4px"
  auth-submit:
    fontSize: "15px"
    fontWeight: 600
    lineHeight: "22px"
  row-title:
    fontSize: "16px"
    fontWeight: 600
    lineHeight: "23px"
  body:
    fontSize: "15px"
    lineHeight: "23px"
  hint:
    fontSize: "13px"
    lineHeight: "20px"
  label:
    fontSize: "14px"
    fontWeight: 500
    lineHeight: "21px"
  status:
    fontSize: "12px"
    fontWeight: 500
    lineHeight: "18px"
  input:
    fontSize: "16px"
rounded:
  skeleton-bar: "4px"
  status: "6px"
  role: "8px"
  control: "10px"
  record: "12px"
  group: "16px"
spacing:
  compact: "4px"
  small: "8px"
  medium: "12px"
  field-inline: "14px"
  row: "16px"
  screen: "20px"
  section: "24px"
  roomy: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "12px 18px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "12px 18px"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.input}"
    rounded: "{rounded.control}"
    padding: "12px 14px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.record}"
    padding: "20px"
  group:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.group}"
  status-normal:
    backgroundColor: "{colors.normal-surface}"
    textColor: "{colors.normal}"
    typography: "{typography.status}"
    rounded: "{rounded.status}"
    padding: "4px 8px"
  status-high:
    backgroundColor: "{colors.high-surface}"
    textColor: "{colors.high}"
    typography: "{typography.status}"
    rounded: "{rounded.status}"
    padding: "4px 8px"
  status-pending:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.muted}"
    typography: "{typography.status}"
    rounded: "{rounded.status}"
    padding: "4px 8px"
  home-action:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.on-brand}"
    rounded: "{rounded.group}"
    padding: "18px"
  tab-active:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.primary}"
    rounded: "{rounded.group}"
    width: "56px"
    height: "32px"
  button-brand:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.on-brand}"
    typography: "{typography.auth-submit}"
    rounded: "{rounded.record}"
    padding: "0px 18px"
  field-auth:
    backgroundColor: "{colors.bg}"
    textColor: "{colors.text}"
    typography: "{typography.input}"
    rounded: "{rounded.record}"
  skeleton-bar:
    backgroundColor: "{colors.skeleton}"
    rounded: "{rounded.skeleton-bar}"
    height: "14px"
  directory-select:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    height: "52px"
---

# Design System: GraphiScan Android

## Overview

**Creative North Star: "The student-record workspace"**

GraphiScan uses white surfaces, recognizable blue identity and cool paper backgrounds to keep student records and the next role-appropriate task easy to scan. The user chose a clean, professional interface with consistent typography, spacing and alignment. Retain the existing GraphiScan name and supplied logo. The latest proposed login is centered and logo-led after the user delegated reference selection; its implementation awaits user visual feedback and is not approved.

This system applies to the Expo Android application in `graphiscan/mobile-app`, especially its default hosted flow. The Vue admin remains a separate retained web design. Native stack navigation, bottom tabs and native controls provide familiar structure; flat groups and readable record rows provide the recurring visual vocabulary. System type remains native. At the user's request, initial content loading uses a restrained feed-style skeleton pulse implemented with Reanimated and Worklets.

**Key Characteristics:**

- White and blue with quiet cool paper workspaces.
- System typography, clear names and aligned record details.
- Flat grouped rows, restrained status chips and native navigation.
- Functional icons that identify actions, destinations or states.

Source record (2026-10-22): `App.tsx`, `src/ui.tsx`, `WorkspaceUI.tsx`, `HostedHome.tsx`, `SignInPanel.tsx`, `AccountSetup.tsx`, `HostedApp.tsx`, `HostedScreeningActions.tsx`, `LoadingSkeleton.tsx` and `package.json`; direction is recorded in `PRODUCT.md` and `.impeccable/surfaces/graphiscan-mobile-app-src-hostedapp-tsx.md`. Defense minutes were read as product context; this document does not claim that every recommendation has been completed. This is documentation of implemented source. The session reports passing TypeScript and Android Hermes export (1281 modules, 19 assets, approximately 3.4 MB JavaScript bundle), not an APK release. The 29-view fictional Chromium matrix passed without document overflow or page errors at the reviewed phone/desktop widths; browser checks observed the CSS pulse running normally and absent under reduced motion. Login, Home, detail, loading and dark browser captures were visually reviewed. The final logo-corner adjustment is recorded from source; its four login recaptures are a separate follow-up. A fresh adb inventory found zero devices, and no Android device or emulator captures exist. The independent reviewer requested RECAPTURE because native Android screenshots are missing. User visual feedback and native approval remain open. Do not infer live model screening, real consent or operational readiness from this visual system.

## Colors

Blue carries the primary task and selection; ink carries names, and quiet neutrals separate surfaces. The frontmatter records the light palette and the corresponding `useColors()` dark values. No secondary brand accent is introduced.

### Primary

- **GraphiScan brand blue (`brand`)** anchors the login button and Home task surface in both OS schemes. Its darker pressed partner (`brand-pressed`), white foreground (`on-brand`) and pale detail foreground (`brand-muted`) are shared brand roles from `useColors()`. The final brand hue was derived from the supplied logo's sampled dominant blue.
- **Interactive blue (`primary`)** identifies shared buttons, links, action icons and active navigation. It matches brand blue in light mode and becomes lighter in dark mode. **Soft blue (`soft`)** supports selection, avatars and pending states.
- **Blue in dark mode (`primary-dark`)** is a lighter blue with a dark foreground (`on-primary-dark`) on filled shared buttons. OS dark mode changes the palette while retaining blue identity.

### Neutral

- **Cool paper (`bg`)** is the normal workspace background and login input tint; **white (`surface`)** is the login page and the surface for groups, inputs and panels in light mode.
- **Ink (`text`)** is the strongest reading color; **muted slate (`muted`)** is for dates, field hints, record metadata and secondary copy.
- **Quiet divider (`border`)** outlines fields and secondary buttons, and separates adjacent records.
- Dark variants replace these roles together through `useColorScheme()`, including the navigation theme and status bar.
- **Placeholder blue (`skeleton`)** is reserved for loading bars and avatar placeholders; its dark counterpart is distinct from the normal soft-blue selection/identity surface.

### Semantic states

Normal and Validated share the green foreground/surface pair; High Potential and Flagged share the amber pair; other values use muted text on soft blue. Errors use the error foreground. Always retain the written state and the separate Model/Review prefixes where provided; color alone cannot convey the meaning.

**The Blue Task Rule.** Use blue to identify the primary action, navigation selection and interactive text; retain the semantic state pairs for recorded statuses.

The brand roles intentionally remain fixed across OS schemes; the login canvas and fields, workspace, shared controls and metadata use the selected light/dark palette. The Home Android ripple remains the local value `#ffffff22`.

## Typography

**Body and heading font:** the native system family, Roboto on Android. Source does not set `fontFamily`, load a font or establish a separate display face. Frontmatter intentionally records only explicit style values. Numeric style measurements are React Native logical units; `px` is the portable DESIGN.md representation, not a claim about physical device pixels.

### Hierarchy

- **Title:** detail/student headings, profile and setup headings use the title role. Home uses the compact home-title role. Login uses the centered title-auth variant.
- **Heading:** sections and shared headings use the heading role. Workspace section headings have a local line-height of 25; native app-bar titles specify size 18 and weight 600 with native line-height.
- **Action title:** the Home primary task has its own compact prominent title.
- **Row title:** student names and action titles in lists; details below use hint.
- **Body:** record values and explanatory paragraphs. Native weight remains default when none is specified.
- **Label:** field labels and shared button text. Login submit uses the auth-submit role.
- **Hint and status:** secondary record metadata and explicit state chips. Dates use size 12 with line-height 18. Tab labels use size 12 with line-height 16.

The supplied wordmark is represented by the supplied image and text: the app-bar text is size 19, weight 700, tracking -0.4; login text is size 28, line-height 36, weight 700, tracking -0.6. Login centers the supplied 80-unit logo with a local 20-unit corner radius above the wordmark, softening the opaque PNG's white corners in dark mode; Graphi uses text color and Scan uses primary. These branding treatments are not general heading styles. Avatar initials use size multiplied by 0.36 and weight 600.

**The System Type Rule.** Reuse native system type and the observed hierarchy across roles; do not introduce a decorative font or a second typographic identity.

## Layout

Native verification update2026-10-23: API36 GraphiScan_Pixel_6/Expo Go58.0.5
login captures now exist in light/dark and at dark font_scale1.3. SignInPanel
and shared Screen use KeyboardAvoidingView height behavior on Android, retaining
iOS padding and the existing web behavior. The keyboard recapture shows password
and sign-in above the actual IME after a reproduced overlap that scrolling did
not resolve. Other native role/form screens remain unverified. Expo Go automatic
configuration reload produced an EventEmitter startup failure; fresh-process
recovery worked, with the underlying cause still open. This updates the earlier
no-emulator evidence boundary without claiming full native finish approval.

The workspace is a single scrolling column with left and right safe areas and bottom inset protection. The shared content container uses padding 20, gap 20, bottom padding 32 and maximum width 600. FlatList screens reuse that container with gap 0 so rows form a continuous list. Within rows, text occupies the flexible column with `minWidth: 0`; names and statuses can wrap. Action rows have minimum height 80. The main task surface has minimum height 112 with padding 18 and a 14-unit horizontal gap.

The spacing vocabulary is a practical rhythm, not a strict mathematical scale. Shared group contents use 4, 8, 12, 16 and 20; field padding also uses 14. Existing local values include gaps 5, 6, 9 and 10 and button inline padding 18. Login is a vertically balanced, scrollable column: maximum width 460, horizontal padding 28, vertical padding 32 and gap 36 between identity and form. Its main region has gap 24, its form gap is 20, and its logo/wordmark gap is 4. Keep these as local composition values rather than inventing global tokens for every literal.

Navigation fills the native device. Bottom tabs have height 74 plus the bottom safe-area inset, top padding 8, bottom padding equal to the larger of the inset and 10, and item horizontal margins 3. Navigation and password-visibility controls retain their explicit minimum tap dimensions of 48. The app bar does not repeat the page heading in the content.

`App.tsx` creates a browser-only development canvas at viewport widths above 600, limiting the app to 420. This is not an Android tablet breakpoint or desktop product layout. Browser previews at 390 and 320 do not establish native keyboard, camera, back, accessibility scaling or device behavior.

## Elevation & Depth

The documented hosted UI is flat. Shared components define no shadow or elevation tokens, and hosted navigation explicitly hides header shadows. White or dark surfaces, cool paper behind them, rounded grouping, dividers and text hierarchy establish depth. Native controls and navigation retain their platform behavior. The only custom motion recorded here is the initial-loading opacity pulse described with its component below; it does not establish a general transition system.

**The Flat Records Rule.** Separate record groups with surfaces, spacing and quiet dividers; preserve the flat treatment of the implemented hosted workspace.

## Shapes

Shared controls use the control radius; individual bordered records, panels and login fields/buttons use the record radius. Grouped rows, setup cards, selected-tab icon pills and the Home action use the group radius. The login page has no enclosing card, top-corner form inset, blue banner or logo tile. Status chips and the role label use their smaller dedicated radii. Avatars are true circles with radius equal to half their size, rather than another fixed radius token.

Borders are normally one logical unit. Record groups clip their contents so pressed surfaces follow the group silhouette. Shared buttons and fields have minimum height 52; multiline fields have minimum height 110. Login buttons and input frames use minimum height 56 with 54-unit inputs, while setup password frames use 52 with 50-unit inputs. These are observed component variants.

## Components

### Buttons

Primary buttons are clear blue actions with centered readable labels. Secondary buttons use the current surface, primary text and a one-unit quiet border. Both share the control radius and shared padding. Shared pressed opacity is 0.8 and disabled opacity is 0.55; no custom button motion is present. Shared button icons are optional and functional. Login uses the fixed brand and on-brand roles, a brand-pressed background and disabled opacity 0.7, with the auth-submit type role, minimum height 56 and record radius.

### Inputs / Fields

Search refinement2026-10-24: shared Field has an opt-in search presentation with
a20-unit decorative Material search icon, a12-unit icon/text gap, student-name
placeholder and primary-colored focused frame. Accessible labels and existing
submit/filter behavior remain. Hosted directory and upload search, plus legacy
Students/Results, use it. Browser role/typing/Enter/clear checks pass; the separate
native search-field capture remains unverified.

Visible labels sit above bordered native text fields. Shared Field and setup password frames use the surface background; login frames use the lightly tinted bg role and left padding 16. Generic Field uses an 8-unit label gap and the input style in frontmatter; it does not currently implement the explicit focus-border color change used by login and setup password frames. Login and setup turn the frame border primary on focus. Password visibility has a dedicated native press target and a visibility icon. Do not infer a shared custom focus-ring system from those local frames.

### Chips

Status chips are compact text on semantic soft surfaces. They are labels, not filters. Model and expert-review states remain separately attributed on screening rows. Role chips use their own radius and 5-unit vertical / 10-unit horizontal padding.

### Student directory forms and filters

`HostedStudents.tsx`, `HostedStudentEditor.tsx` and `HostedDirectoryControls.tsx` extend the existing workspace. The list header wraps Filters and the teacher-only Add student action. Expanded filters use the shared labelled Field and native School/Grade selectors with 16-unit gaps; the applied search, school and grade are summarized above the records. Filters and opaque paging cursors are server parameters. A response is shown only under the exact query that requested it; initial requests show the existing skeleton pattern and refresh retains the current query's records.

DirectorySelect uses the native picker with an 8-unit label gap, a one-unit border, the control radius and a minimum height of 52. Both its frame and picker explicitly use the current surface color, with text and dropdown icon roles from the same scheme. This fixes the white select background in the dark browser preview. Disabled state uses the native enabled flag. Browser dropdown focus and popup appearance remain platform rendering, not a new custom focus or menu system.

The editor groups identity, age, grade and school with 20-unit gaps; optional eligible-parent selection and its explanation use 12-unit gaps. School changes clear the selected parent. Teacher ownership is server-derived, school moves are unavailable during edits, and other roles have no creation/edit controls. An uncertain creation locks the draft for explicit same-submission retry; an uncertain or conflicting edit requires a current-record reload. A successful receipt offers history and return navigation. These states use existing buttons, notices and record values rather than separate visual variants.

Verification on 2026-10-23: the final 11-view/workflow Chromium recapture passed at 390/320, including the dark picker surface, server filters, creation retry, edit reconciliation and role controls, with zero document overflow or application page errors. All writes were intercepted fictional data. This closes the browser theme recapture; Android keyboard, picker popup, Back, font scaling and hosted writes still require native verification.

### Cards / Containers

Model output, expert review and profile details use surface panels with 20-unit padding, 16-unit gaps and the record radius. Hosted detail panels explicitly remove the base panel border. Setup cards use the group radius and gap 20. Home groups use clipped rows with separators and no shadow; empty states use a padded surface with the group radius.

The latest login source uses a centered logo-led white layout, with a dark counterpart, centered sign-in heading, two labelled fields, a blue action and functional help. The user delegated reference selection; the selected inspiration is [Mobile app Login/Signup UI concept](https://dribbble.com/shots/8759887-Mobile-app-Login-Signup-UI-concept). GraphiScan retains its existing authentication controls and supplied logo; no foreign artwork or unsupported sign-up/social actions are included. This implementation awaits user visual feedback. The earlier blue-header composition is superseded.

### Navigation

React Navigation supplies native stacks and bottom tabs. Selected tabs use primary foreground with a 56-by-32 soft-blue pill behind the icon; the label remains below it. Unselected tabs use muted foreground on a transparent icon backing. Home carries the supplied brand and a profile avatar action in its app bar. Teacher tabs include Screen; experts see Reviews and parents see Reports/Children. Native switches, spinners, scroll views and lists remain native controls. Material icons identify destinations, visibility, selection and actions; no new icon system is introduced.

### Record and choice rows

Action and student rows have 16-unit padding and a flexible two-line text column. Screening rows begin with a 36-unit initials avatar, name and grouped grade/screening-type line, followed by wrapping Model/Review chips and date with 8-unit vertical gaps. Android ripple and pressed soft backgrounds provide immediate feedback; a recent record opens its detail directly. Home joins its loaded student list; results/history use the existing scoped student read to resolve names and grades. When a matching student is unavailable, the visible fallback remains Student plus the record's ID. Detail headings use the scoped student read for name and grade, preserving that fallback and separate model/expert sections. Choice rows use radio semantics and a selected soft background with a primary radio indicator. Selection and disabled opacity are explicit states.

### Loading skeletons

Students refinement2026-10-24: Students/Children now use measured viewport fill
for every hosted role, with the existing80-unit student-placeholder density.
Legacy Students and progress/history also opt in. Native hosted-student preview
captures passed in light and dark/font_scale1.3; four fictional browser cases
verified all-role coverage, motion preferences and request outcomes.

Results refinement2026-10-24: screening list skeletons repeat through the measured
FlatList viewport, using window height until layout is known. Hosted Results,
Reviews, Reports and history share this behavior; legacy Results also supplies
its list height. Inline loaders keep their existing size. Five fictional browser
captures verified viewport coverage, role variants, motion preferences and request
outcomes; native loading-only captures verified light and dark/font_scale1.3 on
GraphiScan_Pixel_6. These captures do not establish the actual screening workflow.

Coverage extension2026-10-23: choice rows echo student/model selectors, field
placeholders reserve the52-unit native control, image placeholders reserve300
units, and heading bars cover dependent student-name reads. Initial hosted and
legacy lists/history/details, agreement, choices, schools, eligible parents and
private images use the same feed-style vocabulary. New dependency scopes clear
the old display before loading; refresh retains current content and its ordinary
refresh feedback. Save/sign-in/upload actions retain truthful progress labels.
Fourteen fictional browser views/workflows passed, including dark320 and reduced
motion. These captures do not establish all native/legacy runtime behavior.

Initial Home records, student lists, screening/history lists, detail records and the agreement gate use the dedicated skeleton color for placeholder bars and avatars on a surface backing. Student lists show three rows with a 40-unit avatar placeholder; screening lists show two rows with a 36-unit avatar and adjacent text placeholders; detail and agreement use one group. Groups use the group radius and clipped contents; each row has padding 16 and gap 12. Bars use the skeleton-bar radius, with default height 14 and local heights 12, 16, 18 and 26 to echo text and status shapes. Widths describe a placeholder pattern rather than real data. A visible loading label, busy progressbar semantics and polite live region announce the state; the decorative bars are hidden from accessibility traversal.

Reanimated (4.7.1) and Worklets (0.13.0), matched to the installed Expo SDK, support the requested pulse. The source animates opacity only: 0% and 100% at 0.5, 50% at 1, duration 1400ms, ease-in-out, repeating. Static opacity is 0.75 until the accessibility preference resolves, when reduced motion is enabled, when the app is not active or when its screen is unfocused. Accessibility and AppState listeners are cleaned up. No layout motion, shimmer gradient, animated dummy content or native performance claim is established. Existing records remain visible while refreshing; FlatList refresh remains native. Other action-level loading indicators retain their native spinner behavior.

The sidecar's self-contained HTML/CSS components are browser translations for the design panel. They resolve the React Native JS colors to literals and show the actual visual relationships. Native icons, ripple, safe-area calculations, font rendering and control behavior require the app runtime. Browser focus-visible outlines in those samples are panel accessibility affordances, not new native design tokens.

### Sign-out confirmation

Manual sign-out uses SignOutAction and a native Modal, with a dialog-labelled
surface, heading, explanation and Cancel/Sign out actions. The shared surface
palette, group radius and24-unit padding retain the existing visual system;
a48%-black scrim separates the dialog from the underlying page. Width is fluid
with24-unit outer inset, maximum420 and a scrolling90%-height cap. It appears
without authored motion. Cancel, Escape and Android Back dismiss it; only the
confirmation calls logout. Recovery forms explain their draft loss. Forced
session expiry/recovery bypasses confirmation. Browser Cancel/Escape, draft
retention and exactly-once confirmation passed; native modal/Back remain open.

Balance correction2026-10-23: actions fill two equal columns aligned with the
text edges, separated by12 units and stretched to matching heights. Equal
borderless columns prevent the secondary button's border from changing its
share of the row. Actions stack below320 logical units or above1.4 font scale;
their minimum height follows the label line-height and padding. Six fictional
light/dark captures at390/320/280 confirmed equal sizing and fit. Native
font-scale/visual recapture remains separate.

## Do's and Don'ts

### Do:

- Do preserve the GraphiScan name, supplied logo and clean white and blue identity.
- Do reuse native system typography, shared spacing and aligned flexible text columns across roles.
- Do label model output and expert review separately and retain truthful loading, empty, error and disabled states.
- Do use native stack navigation, bottom tabs and functional icons for familiar Android tasks.
- Do distinguish source and fictional browser preview evidence from Android runtime approval.

### Don't:

- Don't add ornamental icons, decorative illustration, generic AI motifs or unsupported controls.
- Don't add a decorative font or expand the scoped loading pulse into unrelated ornamental motion.
- Don't apply this mobile system to the retained Vue admin design without a separately authorized change.
- Don't turn screening scores or visual state colors into a diagnosis, model availability promise or release claim.

Not canonized or repaired by this documentation: local composition spacing and the generic Field focus-state gap remain source exceptions, not permission to expand them into new global rules. The centered login is the latest proposed source after delegated reference selection; user visual approval is pending. No decorative kicker, glyph-icon convention, custom shadow or system display face is established. Native finish approval, device behavior and any later reviewer findings remain open until separately evidenced.
