# GRAPHISCAN — PREMIUM INTERACTIVE STORYTELLING WEBSITE
## Master Implementation Prompt for Codex CLI

### YOUR ROLE

Act as a Principal Product Designer, Creative Director, Senior Frontend Engineer, UX Storytelling Specialist, and Software Architect.

You are working inside my existing **GRAPHISCAN** project repository.

Your mission is to design and implement a complete, production-quality, visually exceptional, story-driven public website for GraphiScan.

This website must educate visitors about dysgraphia, introduce GraphiScan, explain how the system works, demonstrate its actual capabilities, establish credibility, and provide a way to download the Android mobile application.

The goal is not to create an ordinary SaaS landing page.

Create a memorable, immersive digital experience that combines:

- Educational storytelling
- Premium editorial web design
- Interactive scroll-based narratives
- Real product demonstrations
- Modern frontend engineering
- Research-oriented credibility
- Clear calls to action
- An accessible Android application download

**Core creative concept: "Every Stroke Tells a Story."**

The website should unfold naturally as the visitor scrolls, moving from understanding handwriting difficulties to discovering how GraphiScan supports early screening and management.

---

# PHASE 1 — UNDERSTAND THE GRAPHISCAN SYSTEM

Before implementing anything, inspect the entire relevant repository.

Do not immediately start generating components.

### 1.1 Repository Investigation

Identify and examine:

- Existing project architecture and folder structure
- Admin website technologies
- Expo / React Native application
- Python backend and API
- CNN model integration
- Supabase PostgreSQL database
- Authentication and authorization
- Available user roles and permissions
- Existing GraphiScan logos and visual assets
- Design system, fonts, and colors
- Existing screenshots or interface assets
- Actual implemented features
- Planned or partially implemented features
- Existing documentation and README files
- Deployment configuration

### 1.2 Known Project Context

GraphiScan is a dysgraphia detection and management system using Convolutional Neural Networks.

Its purpose is to support early screening of handwriting-related difficulties among learners, particularly those in Grades 1–3.

The intended users include:

1. Teachers
2. Parents and Guardians
3. Experts and Specialists
4. System Administrators

Current infrastructure:

- Admin website: Vercel
- Mobile application: Expo / React Native
- Backend API and CNN inference: Render
- Database: Supabase PostgreSQL
- Landing website: To be developed

Existing GraphiScan branding uses a primary blue color:

`#355C8C`

Verify these details against the actual repository.

The codebase is the primary source of truth.

### 1.3 Critical Restrictions

Do not unnecessarily:

- Rewrite the existing admin website
- Modify the mobile application's business logic
- Reconfigure the CNN model
- Migrate the database
- Change authentication workflows
- Break existing APIs
- Modify deployment configurations unrelated to the landing website
- Expose sensitive application data

The landing website must be a separate, maintainable frontend application that integrates appropriately with the existing GraphiScan ecosystem.

---

# PHASE 2 — CREATIVE DIRECTION

## 2.1 Design Philosophy

Create a website that feels like a high-end digital product experience.

Draw inspiration from the design principles of:

- Apple — cinematic product storytelling and visual restraint
- Linear — precision, structure, and refined interactions
- Stripe — polished layout and technical credibility
- Premium editorial websites — typography and narrative flow
- Modern educational technology — clarity and accessibility

Do not directly copy any existing website.

Develop a unique GraphiScan visual identity.

The design should be:

- Sophisticated
- Minimalist
- Professional
- Modern
- Human-centered
- Educational
- Emotionally thoughtful
- Research-oriented
- Visually engaging
- Technically polished

It must be suitable for parents, teachers, researchers, specialists, and academic evaluators.

## 2.2 Avoid Generic AI-Generated Design

Do not create a generic startup template.

Avoid:

- Excessive glowing gradients
- Random floating shapes
- Generic glassmorphism
- Repetitive feature cards
- Excessively rounded containers
- Unnecessary icons
- Excessive shadows
- Cartoon-heavy illustrations
- Fake dashboards
- Meaningless statistics
- Generic AI marketing copy
- Animations that exist only for decoration

Instead, use intentional layouts, sophisticated typography, carefully controlled color, original graphical elements, and purposeful motion.

Every design decision should have a reason.

## 2.3 Visual Identity

Start from the existing GraphiScan branding.

Primary color:

`#355C8C`

Explore complementary colors such as:

- Warm white
- Soft ivory
- Deep navy
- Muted blue
- Slate
- Light neutral gray

Use these only if they harmonize with the actual branding.

Typography should combine strong editorial display text with exceptionally readable body text.

Establish consistent:

- Spacing tokens
- Typography scales
- Color tokens
- Border treatments
- Component states
- Animation timing
- Layout widths
- Responsive breakpoints

Create a cohesive visual system rather than designing each section independently.

---

# PHASE 3 — STORYTELLING EXPERIENCE

The website must follow a compelling educational and product narrative.

The visitor journey should be:

**Curiosity → Understanding → Empathy → Discovery → Confidence → Action**

The site should feel like a single unfolding story rather than a stack of disconnected marketing sections.

## ACT I — THE OPENING

### "Every Stroke Tells a Story."

Create an exceptionally strong hero experience.

Concept:

A handwriting stroke gradually appears on screen, potentially forming a meaningful word or phrase.

The animation should be subtle, elegant, and technically efficient.

Suggested opening copy:

**Every Stroke Tells a Story.**

"Sometimes, putting that story into writing isn't easy."

Follow this with a concise introduction to GraphiScan.

Example positioning:

"Intelligent handwriting screening designed to support early understanding and informed intervention."

Refine this wording to reflect the actual system and avoid unsupported claims.

### Hero Requirements

- Full-screen or near-full-screen presentation
- Beautiful editorial typography
- Strong visual hierarchy
- Interactive handwriting-inspired graphic
- Responsive composition
- Clear product branding
- Subtle motion
- Accessible contrast
- Excellent loading performance

Primary CTA:

**Discover GraphiScan**

Secondary CTA:

**Download the App**

Include intuitive navigation without overwhelming the opening experience.

The first impression should communicate professional educational technology, not a generic school project.

---

## ACT II — WHEN WRITING BECOMES DIFFICULT

Introduce the challenges some children experience with handwriting.

As the visitor scrolls, gradually explore concepts such as:

- Letter formation
- Letter sizing
- Spacing and alignment
- Handwriting consistency
- Legibility
- Writing fluency
- Difficulties expressing thoughts through writing

Use interactive visual explanations where appropriate.

For example:

A handwritten word appears normally, followed by a carefully explained illustration of inconsistent spacing or letter formation.

Do not present these examples as proof of dysgraphia.

The goal is educational understanding, not visual diagnosis.

### Interaction Concept

Create a sequence where one handwriting concept is introduced at a time.

Motion may include:

- Progressive strokes
- Line alignment illustrations
- Letter positioning changes
- Text reveal animations
- Controlled scroll transitions

Make sure the educational content remains understandable without animations.

---

## ACT III — UNDERSTANDING DYSGRAPHIA

Develop a dedicated educational section.

Explain:

- What dysgraphia is
- How it may affect handwriting and written expression
- Why handwriting difficulties deserve appropriate attention
- Why early identification and support may be valuable
- How dysgraphia differs from simply having untidy handwriting
- Why proper professional evaluation matters

Maintain a respectful, compassionate tone.

Never suggest that dysgraphia means:

- Low intelligence
- Laziness
- Lack of effort
- Poor character
- An inability to learn

Use plain language that parents and teachers can easily understand.

### Scientific Accuracy

Use trustworthy educational or professional references for factual claims.

Never invent sources or statistics.

Clearly distinguish between educational screening and professional diagnosis.

GraphiScan must not be presented as a replacement for qualified assessment.

---

## ACT IV — INTRODUCING GRAPHISCAN

After establishing the problem, gradually reveal the actual GraphiScan system.

Make this transition one of the website's strongest visual moments.

### Product Reveal

Introduce:

- Official GraphiScan logo
- Actual product branding
- Concise system description
- Purpose and intended users
- Real application screens
- Actual verified capabilities

Possible headline:

**Meet GraphiScan.**

"Technology designed to support understanding, screening, and informed action."

Adjust the wording based on actual implementation.

### Visual Concept

Use an elegant transition from the educational handwriting visuals into the real GraphiScan interface.

For example:

A handwriting sample becomes a visual bridge toward the application's upload or analysis interface.

If implementing this exact transition is impractical, create a simpler but similarly meaningful effect.

Use genuine screenshots or accurate interface presentations from the repository.

Do not invent functionality.

---

## ACT V — HOW GRAPHISCAN WORKS

Create an interactive product walkthrough.

Inspect the actual system to determine its correct end-to-end workflow.

Potential stages include:

1. Authorized users access GraphiScan.
2. A handwriting sample is captured or uploaded.
3. The application sends the sample for processing.
4. The CNN-based pipeline analyzes the handwriting image.
5. Available screening information is presented.
6. Authorized users review results and available guidance.
7. Relevant records support follow-up and monitoring.

These are proposed steps, not confirmed features.

Validate every step against the codebase before presenting it.

### Interaction Design

Consider:

- Interactive step navigation
- Animated workflow progression
- Mobile application previews
- Desktop interface previews
- Smooth screenshot transitions
- Contextual descriptions
- Simple processing diagrams

Avoid overwhelming technical explanations.

The goal is to make the workflow understandable to someone who has never used GraphiScan.

### Product Authenticity

Use actual application screens where possible.

If a feature is incomplete, do not advertise it as finished.

Do not invent successful predictions or fabricated model outputs.

---

## ACT VI — BUILT FOR THOSE WHO SUPPORT LEARNERS

Create a premium, role-based feature exploration section.

Show how the platform supports its different intended users.

### Teachers

Explain the actual teacher-facing features, potentially including handwriting submissions, learner management, and available screening information.

Verify implementation.

### Parents and Guardians

Explain the real functionality available to authorized parents and guardians, especially how they view screening information or recommendations.

### Experts and Specialists

Explain the implemented role of specialists, including any review, validation, or recommendation workflows supported by the codebase.

### System Administrators

Introduce the existing administrative interface and its actual responsibilities.

### Recommended UI Pattern

Implement interactive role tabs or a carefully designed segmented interface.

Selecting a role should display:

- Role name
- Clear explanation
- Verified capabilities
- Real corresponding application screenshot
- Relevant workflow information

All interactions must be keyboard-accessible.

Avoid falsely presenting all users as having the same permissions.

---

## ACT VII — THE TECHNOLOGY BEHIND GRAPHISCAN

Explain the system's technical foundation clearly and responsibly.

GraphiScan uses CNN-based handwriting image analysis.

Investigate and describe the actual implemented processing pipeline.

Potential components:

- Image acquisition
- Image preprocessing
- Model inference
- Screening output
- Authorized record storage
- Result presentation

Only include components that are actually implemented or clearly described as planned.

### Visual Direction

Create an elegant explanatory diagram.

Possible structure:

Handwriting Sample → Image Processing → CNN Analysis → Screening Information

Verify whether this reflects the real backend pipeline.

The visualization should prioritize comprehension over visual complexity.

Explain the role of AI without suggesting that the system can independently provide a clinical diagnosis.

Do not display invented model accuracy metrics.

Do not expose private backend internals or sensitive data.

---

## ACT VIII — EXPERIENCE THE ACTUAL APPLICATION

Build a dedicated visual product showcase.

This should be one of the strongest visual sections of the website.

Use the best actual GraphiScan interface screens from:

- The Expo mobile application
- The administrator website
- Other verified role-specific interfaces

### Presentation Ideas

- Realistic mobile device frames
- Desktop browser mockups
- Scroll-triggered screen transitions
- Interactive screenshot galleries
- Alternate image-and-text layouts
- Short explanatory captions

Create a sophisticated presentation without distorting the real interface.

Do not manufacture screenshots containing nonexistent features.

If necessary, add clear temporary placeholders for screenshots that need to be captured later.

Never display genuine learner records or personally identifiable information in public-facing visuals.

---

## ACT IX — DOWNLOAD GRAPHISCAN

Create a polished, highly visible Android application download experience.

The app is distributed directly through the website instead of the Google Play Store.

### Required Features

- Clear "Download for Android" action
- Dedicated download section
- Dedicated `/download` page
- Application version when available
- APK file size when available
- Release information when available
- Installation instructions
- Mobile-friendly presentation
- QR code linking to the download page
- Link to the existing admin login where appropriate

### Download Behavior

The application must link to a valid signed APK when available.

Investigate whether the repository already contains an appropriate Expo EAS Build workflow or existing APK release artifacts.

Do not confuse APK and AAB formats.

If no APK is currently available, display an accurate unavailable or upcoming-release state.

Do not create a fake download link.

Do not claim that the application is available on Google Play.

Do not suggest that an Android APK can be installed on iOS.

### Installation Guide

Provide simple instructions explaining how an Android user can:

1. Download the APK.
2. Open the downloaded file.
3. Allow installation from the selected source if Android requests it.
4. Complete installation.
5. Open GraphiScan.

Keep the instructions accurate, understandable, and mindful of Android security warnings.

The download experience must look like part of the same premium product, not an unrelated file-hosting page.

---

## ACT X — RESEARCH, TRUST, AND RESPONSIBLE USE

Create a dedicated section establishing GraphiScan's credibility.

Potential topics:

- The purpose of the GraphiScan project
- The research and development background
- The intended educational context
- The role of professional evaluation
- Limitations of automated screening
- Privacy and responsible data handling

Only present information supported by project documentation.

Do not invent:

- Partner organizations
- Research endorsements
- Certifications
- Clinical approval
- Institutional recognition
- User testimonials
- Model performance statistics

If official research team details or institutional affiliation are available and appropriate for public use, present them professionally.

### Privacy Considerations

GraphiScan may process children's handwriting and associated learner information.

Handle all demonstrations and public content carefully.

Do not:

- Display genuine learner data publicly
- Expose confidential student records
- Include private authentication tokens
- Reveal database secrets
- Promise absolute data security
- Invent privacy compliance certifications

Public educational content and private application data must remain separate.

---

## ACT XI — FREQUENTLY ASKED QUESTIONS

Create an accessible FAQ section.

Suggested questions:

- What is GraphiScan?
- What is dysgraphia?
- Who is GraphiScan designed for?
- Can GraphiScan diagnose dysgraphia?
- How does the handwriting screening process work?
- Does GraphiScan use artificial intelligence?
- Is the Android application available for download?
- How do I install GraphiScan?
- Can parents view learner screening information?
- How is learner information handled?

Answers must accurately reflect the implemented system and verified project documentation.

Use an accessible accordion design with smooth, restrained interactions.

---

## ACT XII — THE FINAL MESSAGE

Close the storytelling experience with an emotionally meaningful but responsible message.

Reconnect with the hero section's handwriting motif.

Possible headline:

**Every Learner Deserves to Be Understood.**

Supporting message:

"Understanding handwriting challenges is a step toward providing meaningful support."

Refine the final copy to reflect the system's purpose.

Include strong, clear actions:

- Download GraphiScan
- Explore How It Works

Finish with a professional footer containing verified project information, navigation, and relevant legal or contact links.

The ending must feel intentional and memorable.

---

# PHASE 4 — INFORMATION ARCHITECTURE

Recommended routes:

`/`

Main interactive storytelling homepage.

`/download`

Dedicated Android download experience and installation information.

`/about`

Project background, objectives, and verified team information.

`/privacy`

Privacy information using reviewed and accurate project content.

`/terms`

Only if applicable terms have been prepared and approved.

Do not generate misleading legal policies.

Determine whether additional pages are necessary based on content and UX quality.

Prefer a focused architecture over unnecessary route proliferation.

### Main Navigation

Suggested items:

- Discover
- Understanding Dysgraphia
- How It Works
- Features
- Download
- About

Provide access to the existing admin portal without implying that its private pages are publicly accessible.

The navigation should remain simple and effective on mobile devices.

---

# PHASE 5 — MOTION DESIGN

Motion is an important part of the storytelling experience.

However, motion must support meaning.

### Recommended Animation Concepts

1. Progressive handwriting stroke animation in the hero
2. Elegant heading and paragraph reveals
3. Scroll-driven educational illustrations
4. Product reveal animation
5. Step-by-step workflow transitions
6. Smooth interface screenshot transitions
7. Subtle navigation microinteractions
8. Restrained hover effects
9. Meaningful closing animation

### Animation Technologies

Investigate the existing stack before adding dependencies.

Consider:

- CSS animations and transitions
- Intersection Observer
- GSAP with ScrollTrigger for complex storytelling
- Motion libraries only where justified

Use the simplest appropriate tool.

Do not install multiple animation libraries without a clear reason.

### Performance and Accessibility Rules

- Respect `prefers-reduced-motion`.
- Avoid unnecessary scroll hijacking.
- Minimize animation work on mobile devices.
- Prevent layout shift.
- Use transforms and opacity for suitable animations.
- Ensure keyboard navigation remains usable.
- Maintain readable content without JavaScript-heavy effects.
- Avoid large, unnecessary animation bundles.

A beautiful website should also feel fast.

---

# PHASE 6 — FRONTEND ARCHITECTURE

Inspect the existing repository before selecting the implementation approach.

If there is no existing suitable landing site, consider:

- Next.js
- React
- TypeScript
- Tailwind CSS
- A carefully selected animation solution
- Reusable components
- Centralized design tokens

Prefer a standalone application within the existing repository when appropriate.

Do not migrate existing projects simply to achieve technology consistency.

### Component Architecture

Use well-defined sections and components.

Potential structure:

- Site layout
- Header
- Mobile navigation
- Hero
- Handwriting narrative
- Dysgraphia education
- GraphiScan reveal
- How-it-works walkthrough
- User role explorer
- Technology explanation
- Product showcase
- Download section
- FAQ
- Final CTA
- Footer

Make the exact folder structure compatible with the repository.

### Code Quality Expectations

- Type-safe implementation
- Clear component responsibilities
- Reusable UI primitives
- Maintainable styles
- Responsive layouts
- Accessible semantic markup
- Minimal unnecessary dependencies
- No dead code
- No placeholder features pretending to work
- No unnecessary global state
- Consistent naming conventions
- Proper error and empty states

Use the repository's established coding conventions wherever possible.

---

# PHASE 7 — PERFORMANCE, ACCESSIBILITY, AND SEO

Implement production-quality engineering practices.

### Performance

- Optimize images and graphics.
- Avoid oversized client-side bundles.
- Lazy-load appropriate media.
- Minimize layout shifts.
- Prioritize initial content rendering.
- Use efficient animation techniques.
- Optimize font loading.
- Keep page interactions responsive.

Aim for strong Core Web Vitals without inventing performance scores.

### Accessibility

- Semantic HTML
- Logical heading hierarchy
- Keyboard-accessible navigation
- Visible focus states
- Sufficient color contrast
- Descriptive alternative text
- Accessible accordions and tabs
- Responsive text scaling
- Reduced-motion support
- Clear download instructions

### SEO

- Descriptive metadata
- Appropriate page titles
- Search-friendly educational content
- Open Graph metadata
- Social sharing image where assets are available
- Semantic page structure
- Canonical configuration when the final public URL is known
- Sitemap and robots configuration when appropriate

Avoid publishing incorrect canonical URLs or placeholder production metadata.

---

# PHASE 8 — APPLICATION INTEGRATION

The landing website should complement the existing GraphiScan applications, not replace them.

### Admin Application

Provide an appropriate link to the existing admin portal.

Reuse the existing admin application URL through configurable application settings.

Do not create an unnecessary second admin dashboard.

### Mobile Application

Present the real Expo mobile application.

Use actual screenshots when possible.

Connect the download experience to a valid APK artifact when available.

Avoid making changes to existing mobile business logic.

### Backend

Do not connect the public landing website directly to protected screening or learner endpoints unless there is an explicit and secure product requirement.

Most educational and marketing content should be independently renderable.

### Database

Do not modify the Supabase database merely to support static landing page content.

If release metadata or public content requires a data source, evaluate the simplest secure solution.

### Configuration

Keep configurable values centralized, including:

- Public website URL
- Existing admin portal URL
- Android APK download URL
- App version
- App release information
- Public contact information

Do not hardcode secrets.

Do not expose Supabase service-role credentials or private backend keys.

---

# PHASE 9 — IMPLEMENTATION WORKFLOW

Follow a disciplined development process.

## Step 1 — Audit the Repository

Identify the real application structure, existing assets, design language, user roles, and implemented features.

Report a concise summary of your findings.

## Step 2 — Establish the Landing Site Architecture

Select the appropriate location and implementation framework.

Protect the existing applications from unnecessary modifications.

## Step 3 — Establish the Visual System

Implement:

- Color tokens
- Typography
- Layout system
- Spacing system
- Buttons and navigation
- Motion conventions
- Shared components

## Step 4 — Build the Storytelling Homepage

Implement every major narrative section in the defined visitor journey.

Use meaningful, accurate content.

Do not stop at a hero section or simple wireframe.

## Step 5 — Integrate Authentic Product Content

Reuse:

- Existing GraphiScan branding
- Verified features
- Real user roles
- Actual application screenshots
- Accurate workflow information

## Step 6 — Build the Download Experience

Implement the dedicated download route, release information, installation guide, QR code, and configurable APK link.

Ensure unavailable releases have a truthful state.

## Step 7 — Polish the Experience

Improve:

- Animation pacing
- Typography
- Transitions
- Visual composition
- Responsive layout
- Interaction details
- Mobile usability

The experience should feel cohesive from the first screen to the footer.

## Step 8 — Test and Validate

Run the relevant checks:

- Type checking
- Linting
- Production build
- Internal navigation
- Responsive design
- Accessibility
- Reduced-motion behavior
- Download URL behavior
- Console and runtime errors

Use browser-based visual checks if supported by the environment.

Test common mobile and desktop viewport sizes.

Fix problems introduced by the new implementation.

Before terminal commands, explain what each command does and why relevant flags are needed.

## Step 9 — Document the Result

Provide:

- Summary of implemented features
- Created and modified files
- Component architecture
- Local development instructions
- Build instructions
- Required configuration
- Deployment instructions for Vercel
- APK update procedure
- Missing assets or content requiring review
- Remaining known limitations

Do not automatically publish, deploy, purchase services, or commit changes without authorization.

---

# PHASE 10 — DESIGN QUALITY REVIEW

Before considering the website complete, evaluate it from several perspectives.

### Creative Director Review

- Is the visual identity memorable?
- Does the design look professionally art-directed?
- Are section compositions distinctive?
- Is motion purposeful?
- Does the product reveal feel satisfying?
- Does the website avoid generic template patterns?

### Product Designer Review

- Can first-time visitors understand GraphiScan?
- Is the dysgraphia explanation accessible?
- Is the narrative logically connected?
- Are the calls to action obvious?
- Is the download experience straightforward?
- Does the mobile experience remain intuitive?

### Engineering Review

- Is the architecture maintainable?
- Are components reusable?
- Is the application performant?
- Are interactions accessible?
- Is the code type-safe?
- Are dependencies justified?
- Is existing functionality preserved?

### Research and Content Review

- Are medical and educational statements responsible?
- Are features grounded in the repository?
- Are there unsupported claims?
- Is screening clearly distinguished from diagnosis?
- Is learner privacy respected?

Improve weak areas before finalizing.

---

# NON-NEGOTIABLE REQUIREMENTS

The finished website must:

1. Be a complete working frontend implementation.
2. Tell a coherent story about handwriting, dysgraphia, and GraphiScan.
3. Create an emotionally engaging but scientifically responsible experience.
4. Feature sophisticated, premium visual design.
5. Include purposeful scroll-based animation.
6. Use actual GraphiScan branding.
7. Accurately demonstrate the existing product.
8. Support teachers, parents, specialists, and administrators through truthful descriptions.
9. Include a complete Android download experience.
10. Preserve all existing applications and services.
11. Work on desktop, tablet, and mobile.
12. Respect accessibility and reduced-motion settings.
13. Follow strong frontend engineering practices.
14. Avoid fake features, testimonials, statistics, and unsupported claims.
15. Be suitable for public presentation and academic evaluation.

Do not build a generic template and claim the task is complete.

Do not prioritize decorative complexity over clarity.

Do not implement attractive visuals that misrepresent the actual product.

---

# FINAL CREATIVE BRIEF

The GraphiScan website should feel like a carefully crafted digital story.

The opening should make visitors curious about handwriting.

The next sections should help them understand that writing difficulties can be complex and deserve thoughtful attention.

The product reveal should introduce GraphiScan naturally, showing how technology can contribute to early screening and support.

The walkthrough should make the system understandable.

The application showcase should make the product tangible and credible.

The download experience should make getting started simple.

The closing should leave visitors with a meaningful understanding of GraphiScan's purpose.

Above all:

**Build a website that helps people understand the problem before introducing the technology.**

Make GraphiScan feel like a coherent, thoughtful, professionally engineered educational technology product.

The final outcome should be distinctive, beautiful, responsive, accessible, credible, and fully functional.

## BEGIN

Start by inspecting the actual GraphiScan repository.

Identify the safest implementation architecture, establish the creative direction, and build the complete landing website according to this specification.

Make reasonable engineering and design decisions independently. Do not interrupt implementation for minor preferences that can be resolved through established best practices.

Preserve existing system functionality and clearly report any blockers or items requiring review.