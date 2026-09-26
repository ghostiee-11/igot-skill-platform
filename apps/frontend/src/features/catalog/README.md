# Catalog Feature Module

The **Catalog** feature module owns course discovery, search filtering, and course detail screens on the **iGOT Karmayogi (MoSPI)** platform.

---

## 1. Responsibilities & Route Ownership
- `/discover` (`DiscoverPage.tsx`): Main national course catalog and external accredited training explorer.
- `/courses/[courseId]` (`CourseDetailPage.tsx`): Comprehensive course overview, module/lesson syllabus breakdown, and enrollment action handlers.
- Route wrappers (`frontend/src/app/discover/page.tsx`, `frontend/src/app/courses/[courseId]/page.tsx`) delegate directly to these components without owning domain logic.
- Maintains Next.js build compatibility by wrapping search parameter consumers inside React `<Suspense>` boundaries.

---

## 2. Institutional Design Standards
- **Color Tokens:** Aligned with the official Navy Blue (`#1E3A8A`) and Sober Yellow (`#EAB308`) institutional standard.
- **Layout Architecture:**
  - Header: Full-width white section (`bg-white border-b border-slate-200`) with letter-spaced ministry eyebrow text and Lucide `Building2` iconography.
  - Workspace Canvas: Continuous `#F8FAFC` slate canvas housing the filter ribbon, segmented discipline tabs, and course cards grid.
- **Zero Decorative Emojis:** All decorative unicode emojis (`🔥`, `✨`, `★`) and artificial rectangular colored eyebrow pills are strictly banned. Uses curated Lucide SVG icons (`Building2`, `Search`, `Clock`, `Star` with warm yellow fill, `UserCheck`, `ShieldCheck`, `CheckCircle2`, `Award`).
- **Accreditation Trust Ribbon:** Institutional accreditation footer affirming MoSPI accreditation, CBC competency guidelines, and verifiable cryptographic credentials.

---

## 3. Bilingual (Hindi & English) Localization
- Completely integrated with `useI18n()` from `@/lib/i18n`.
- Dynamic language switching dynamically re-renders:
  - Search input placeholder and action buttons (`खोजें` / `साफ़ करें`).
  - Trending search queries (e.g. *राष्ट्रीय नमूना सर्वेक्षण*, *उपभोक्ता मूल्य सूचकांक*, *सीएपीआई क्षेत्रीय सत्यापन*).
  - Discipline category tabs (e.g. *डेटा प्रशासन*, *डेटा विज्ञान*, *मूल्य सांख्यिकी*, *लोक प्रशासन*, *नमूना सर्वेक्षण*).
  - Filter options (*सभी प्रदाता*, *सभी कठिनाई स्तर*, *क्रमबद्ध करें:*, *सर्वाधिक नामांकित*).
  - Course card metadata, titles, descriptions, accredited bodies, and `पाठ्यक्रम देखें >` CTAs.
