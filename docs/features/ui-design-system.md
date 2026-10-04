# UI/UX Design System: Navy Blue & Extended Institutional Palette

2026-10-04 local follow-up: active styles are under `apps/frontend/src/app/globals.css`. Dark hero glass actions use the semantic `--color-hero-action-hover` token (white at 16% opacity) on hover and keyboard focus; labels/icons remain light. This replaces the obsolete opaque light-hero hover remap. My Learning was verified in the rebuilt local frontend.

> **Status:** `Implemented` (Design Branch / Design System v3.0)  
> **Primary Files:**  
> - Styles: `frontend/src/app/globals.css`  
> - Components: `Navbar.tsx`, `Footer.tsx`, `AiAssistantWidget.tsx`, `EntryLandingPage.tsx`, `HomePage.tsx`, `DiscoverPage.tsx`

---

## 1. Executive Summary & Design Philosophy

The **iGOT Karmayogi (MoSPI)** platform adheres to an authoritative institutional design standard — **"The credibility of granite, the energy of tomorrow."** Think how a premier institution like ISRO or RBI would present itself digitally: grounded, trustworthy, yet modern and exciting.

**v3.0 Design Principles:**
- **Institutional Drama:** The primary pages (landing, home, discover) open with dark navy-to-teal gradient hero sections with CSS mesh-grid overlays and radial glow orbs — establishing authority immediately.
- **Color Variety Without Chaos:** A 5-color extended palette (navy, teal, ochre, amber, sage) gives each section/feature a distinct visual identity without descending into pastels or neon.
- **Defeated Rectangle Monotony:** Cards use left-border accents, top-stripe accents, and colored icon containers. Never all the same border-slate-200 box pattern.
- **Motion as Signal:** 8 CSS-only `@keyframe` animations (no JS libraries). `pulseGlow` on the AI button signals it's alive. `floatDot` creates a typing indicator. `fadeInUp` staggers page entrance. All disabled by `prefers-reduced-motion`.
- **Glassmorphism Restraint:** Used only on dark gradient backgrounds (`glass-light`, `glass-card` utilities) — not on white-background sections where it would look out of place.
- **Zero AI Telltales:** No emojis in content, no colored pill boxes above headings, no generic pastel cards.

---

## 2. Design System Color Tokens

### 2.1 Navy Primary Scale
| Token | CSS Variable | Hex | Use |
|---|---|---|---|
| Navy Primary | `--color-navy-primary` | `#1E3A8A` | Brand actions, key buttons, borders |
| Navy Hover | `--color-navy-hover` | `#172554` | Hover states |
| Navy 700 | `--color-navy-700` | `#1E3570` | Mid-depth navies |
| Navy Deep | `--color-navy-deep` | `#0F2C59` | Gradient anchors |
| Navy 900 | `--color-navy-900` | `#0C1B3D` | Hero gradient via |
| Navy Darkest | `--color-navy-darkest` | `#070E20` | Hero gradient start |

### 2.2 Accent Scale (v3.0 additions)
| Token | CSS Variable | Hex | Use |
|---|---|---|---|
| Teal 600 | `--color-teal-600` | `#0D9488` | Progress bars, teal accents, AI widget, typing indicator |
| Teal 500 | `--color-teal-500` | `#14B8A6` | Lighter teal highlights |
| Teal 50 | `--color-teal-50` | `#F0FDFA` | Teal section backgrounds |
| Ochre 500 | `--color-ochre-500` | `#B45309` | Resource cards, FAQ, warm accents |
| Ochre 50 | `--color-ochre-50` | `#FFFBEB` | Ochre section fills |
| Sage 600 | `--color-sage-600` | `#059669` | Success, streak, beginner-level indicators |
| Sage 50 | `--color-sage-50` | `#ECFDF5` | Sage fills |

### 2.3 Gradient Utilities (v3.0)
| Class | CSS | Use |
|---|---|---|
| `.hero-gradient` | `linear-gradient(135deg, #070E20, #0C1B3D, #1E3A8A, #0D9488)` | Page hero backgrounds (landing, home, discover) |
| `.navy-teal-gradient` | `linear-gradient(135deg, #1E3A8A, #0D9488)` | Buttons, brand icon, avatar ring, chat header |
| `.hero-mesh` | CSS background-image grid | Pattern overlay on dark gradient sections |

### 2.4 Gold / Yellow
| Token | Hex | Use |
|---|---|---|
| Gold Primary | `#EAB308` | CTA register button, milestone numbers |
| Gold Hover | `#CA8A04` | Gold hover states |
| Gold Light | `#FEF9C3` | Background tints |

---

## 3. Animation System (v3.0)

All animations are defined as CSS `@keyframe` rules in `globals.css` with corresponding utility classes:

| Class | Keyframe | Duration | Use |
|---|---|---|---|
| `.animate-fade-in-up` | `fadeInUp` | `0.5s` | Page section entrance |
| `.animate-fade-in-up-delay-{1,2,3}` | `fadeInUp` | `0.5s + delay` | Staggered hero content |
| `.animate-pulse-glow` | `pulseGlow` | `2.5s infinite` | AI assistant floating button |
| `.animate-float-dot{,-2,-3}` | `floatDot` | `1.4s infinite + delay` | Chat typing indicator |
| `.animate-shimmer` | `shimmer` | `2.5s infinite` | Subtle gradient movement |
| `.animate-marquee` | `marquee` | `35s linear infinite` | Horizontal scrolling content |
| `.card-hover-lift` | CSS transition | `0.2s ease` | All cards — translateY(-3px) on hover |

> **Accessibility:** `@media (prefers-reduced-motion: reduce)` disables all animations globally.

---


## 3. Structural & Interaction Patterns

### 3.1 Single-Viewport Section Architecture (`frontend/src/features/landing/components/EntryLandingPage.tsx`)
Landing page sections (`#hero`, `#about`, `#how-it-works`, `#resources`, `#help`) are styled with:
```tsx
className="scroll-mt-16 sm:scroll-mt-[68px] min-h-[calc(100vh-68px)] flex flex-col justify-center"
```
Clicking any navigation item glides directly to and frames that section cleanly in the viewport without awkward cutoffs or extra blank spaces.

### 3.2 Precision Smooth Scrolling & Trackpad Momentum
- **Elimination of Compounding Offsets:** Rely solely on `scroll-mt-[120px]` matching the sticky header height.
- **Inertia Physics Preservation:** Programmatic transitions use `window.scrollTo({ behavior: "smooth" })` on anchor clicks while avoiding global CSS scroll-behavior that interferes with macOS trackpad inertia.
- **Scroll-Spy Lock:** Employs `isProgrammaticScrollRef` during anchor gliding to prevent intermediate tabs from flickering mid-flight.

### 3.3 Zero-Blink & Zero-Shift Tab Navigation (`Navbar.tsx`)
- Standardized fixed 1px borders (`border-transparent` on inactive, `border-blue-200` on active) to eliminate 2–3px box-model layout shifts when toggling tabs.
- Maintained constant `font-medium` across active and inactive states to avoid font-metric width jumps.
- Anchor links configure `scroll={false}` and `prefetch={false}` to prevent Next.js router full-page flickers.

### 3.4 Context-Aware Institutional Footer (`Footer.tsx`)
- Dynamic client component rendering:
  - Omitted on the landing page (`pathname === "/"`) so that `#help`'s integrated dark CTA and legal ribbon sits flush at the bottom.
  - Automatically rendered on all inner views (`/discover`, `/login`, `/register`, `/home`, etc.).

### 3.5 Catalogue Workspace Architecture (`DiscoverPage.tsx` & `CourseDetailPage.tsx`)
- **Full-Width Institutional Header (`bg-white border-b border-slate-200`):** Replaced isolated floating widget cards with full-bleed institutional banners featuring clean letter-spaced ministry eyebrow text and Lucide `Building2` iconography.
- **Slate Workspace Canvas (`bg-[#F8FAFC]`):** The catalog grid and filter ribbon live directly on the clean `#F8FAFC` slate canvas with crisp white course cards (`bg-white border border-slate-200 shadow-2xs`).
- **Unified Action Buttons:** All primary course exploration and enrollment CTAs standardize on Official Navy Primary (`bg-[#1E3A8A] hover:bg-[#172554] text-white`).
- **Complete Bilingual i18n Integration:** Every text element, filter option, search input, topic badge, and course title dynamically responds to the Navbar's `useI18n()` language toggle.

### 3.6 Post-Login Dashboard & All Pages Standardization (`/home`, `/my-learning`, `/profile`, `/admin`)
- **Seamless White Institutional Headers:** Replaced nested floating widget cards with full-width white institutional banners across the entire post-login application.
- **Continuous Slate Canvas (`#F8FAFC`):** Workspaces sit on a continuous `#F8FAFC` neutral canvas, eliminating fragmented multi-colored boxes and dark hero gradients.
- **Strict Elimination of Artificial "AI Telltales":** Removed decorative unicode emojis (`🔥`, `✨`, `★`, `🎉`), text checkmarks (`Completed ✓`), and colored rectangular pill badges above headings. Status indicators use semantic Lucide SVG icons (`CheckCircle2`, `XCircle`, `ShieldCheck`).
- **Primary Navy Brand Standardization:** Standardized interactive buttons and action controls across all pages and modals onto Official Navy Primary (`bg-[#1E3A8A] hover:bg-[#172554]`).
- **100% Bilingual Hindi/English Support:** Full dictionary coverage in `frontend/src/lib/i18n/index.tsx` for post-login dashboard, learning transcript, official profile, and administrative console.

### 3.7 Standalone Institutional Pages (`/about`, `/how-it-works`, `/resources`, `/help`)
- **Feature Components:** `frontend/src/features/institutional/components/` contains `AboutPage.tsx`, `HowItWorksPage.tsx`, `ResourcesPage.tsx`, and `HelpPage.tsx`.
- **Route Files:** `frontend/src/app/{about,how-it-works,resources,help}/page.tsx` each import and render their respective institutional component.
- **Consistent Layout Pattern:** Every page follows the same structure:
  1. **White Institutional Header Banner** (`bg-white border-b border-slate-200 py-8 sm:py-12`): Ministry eyebrow text with `Building2` icon, `h1` title via `useI18n()`, subtitle, and action buttons (Explore Catalogue + Dashboard if authenticated).
  2. **Continuous Slate Canvas** (`bg-[#F8FAFC]`): Main content area with `max-w-6xl mx-auto` grid sections.
- **Content Architecture:**
  - **About:** 3 competency pillar cards, rule-based vs. role-based paradigm comparison, 6 stakeholder governance cards (MoSPI, CBC, NSSTA, NSSO, CSO, ISTM), verifiable credentials dark banner.
  - **How It Works:** 4-stage capacity building cards with full explanations and key standard operations, 3-column process guarantee strip, 2-column FAQ grid, dark closing CTA banner.
  - **Resources:** Search + category filter bar, 6 official document cards with metadata tables and download modals, empty-state handling.
  - **Help:** 3-channel support grid (AI Assistant, Training Desk, Nodal Coordinators), collapsible FAQ accordion, support ticket form with tracking ID simulation.

### 3.8 Context-Aware Navbar Navigation Routing (`Navbar.tsx`)
- **Unauthenticated users on `/` (landing page):** Navbar links render as anchor links (`/#about`, `/#how-it-works`, etc.) with programmatic smooth-scroll via `handleAnchorClick()` and scroll-spy active state tracking.
- **Authenticated users or any non-landing page:** Navbar links render as page routes (`/about`, `/how-it-works`, etc.) navigating to the dedicated standalone institutional pages.
- **Routing Logic:** `href={!user && pathname === "/" ? "/#about" : "/about"}` pattern used across all 4 institutional links in both desktop and mobile menus.
- **Active State Highlighting:** Uses `isActive("/about")` for page routes and `pathname === "/" && activeSection === "about"` for anchor scroll-spy, ensuring correct visual feedback in both modes.

---

## 4. Graphical & Iconography Guidelines

1. **Dual-Tone Icon Badges:** Use curated `lucide-react` icons wrapped in high-contrast dual-tone containers:
   - Primary: `bg-blue-50 text-[#1E3A8A] border border-blue-200`
   - Accent: `bg-amber-50 text-amber-700 border border-amber-200`
2. **Progressive Flow Lines:** Connected workflows utilize smooth gradients (`from-[#1E3A8A] via-blue-400 to-[#F59E0B]`) with numbered step pins.
3. **Aspect Ratio Preservation:** Official institutional media (`/karmayogi.jpg`, `/government-meeting.jpg`, `/ai-daksh.jpg`) MUST retain natural aspect ratios using `object-contain` within framed containers.
4. **Strict Elimination of Emojis & AI Telltales:** All decorative unicode emojis (`🔥`, `✨`, `★`, `🎉`) and artificial rectangular colored pill boxes above headings are strictly disallowed. Use semantic Lucide SVG icons (e.g. `CheckCircle2`, `Building2`, `Clock`, `TrendingUp`) and official typography to maintain constitutional and civil service gravitas.

