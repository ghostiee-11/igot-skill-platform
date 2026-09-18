# iGOT Skill Platform — Documentation

## Service rebuild: start here

- [Architecture](architecture/service-architecture.md) and [service catalogue](services/README.md): boundaries, ownership, interfaces and data.
- [Migration status](migration/status.md) and [data mapping](migration/data-ownership.md): actual verification, baseline, records and rollback.
- [Decisions](decisions/README.md): current architecture decisions.
- [Feature migration catalogue](features/service-migration-catalogue.md) and [known issues](known-issues.md): retained behavior, owners and limits.
- [Lab operations](operations/labs.md): execution boundary and lifecycle.
- Deferred projects: [fresh frontend](plans/frontend-rebuild.md) and [cloud VM labs](plans/cloud-vm-labs.md).

The original navigation below is historical context. Check old paths and completed-feature claims against migration status. Read the owning service contract before changes; update specs/changelog with behavior changes and use ADRs for architectural decisions. No cross-service implementation imports or schema access; no import-time migrations/seeding. Source, tests and migrations outweigh prose. Do not mark scaffolded or unverified features complete.

Welcome to the centralized documentation hub for the **iGOT Karmayogi (MoSPI)** platform, built for the **Smart India Hackathon (SIH '26)**.

This directory provides structured, decentralized knowledge bases for software engineers, evaluators, and AI coding agents.

---

## Documentation Navigation

### 1. [Master Changelog](changelog.md)
The single source of truth for all repository changes made across team members and AI coding agents. Structured chronologically with module attribution (`[frontend]`, `[backend]`, `[devops]`, `[docs]`, `[architecture]`).

---

### 2. [Feature Specifications (`docs/features/`)](features/README.md)
In-depth functional and technical specifications for each subsystem:
- [AI Copilot](features/ai-copilot.md) — LangGraph state machine, provider routing (Gemini/OpenAI), deterministic MoSPI fallback engine, and circular launcher widget.
- [Course Management](features/course-management.md) — Discovery catalog, syllabus hierarchy, Coursera-style split-screen player, in-lesson practice concept checks, and full Hindi compatibility.
- [Assessment & Certification](features/assessment-certification.md) — Timed exams, 70% passing threshold, automatic explanatory grading, celebratory confetti, and verifiable print/PDF certificates.
- [Auth, RBAC & Onboarding](features/auth-rbac.md) — NIST PBKDF2-HMAC security, JWT sessions, pre-seeded evaluation personas, and the 5-step onboarding wizard.
- [Analytics & Dashboards](features/analytics-dashboard.md) — 10-widget learner home dashboard, admin supervisory console, officer roster, and question difficulty analytics.
- [UI/UX Design System](features/ui-design-system.md) — Official Navy Blue (`#1E3A8A`) and Sober Yellow (`#EAB308`) design standard, slate neutral tokens, single-viewport scroll gliding, zero-shift tab navigation, and zero-emoji compliance.
- [Homepage & Public Portal](features/homepage-portal.md) — Institutional landing page (`/`), single-viewport section layout, official photography carousel, connected milestones, and bilingual support.

---

### 3. [Teammate Contribution Logs (`docs/team/`)](team/README.md)
Persistent records tracking both visible repository commits and "invisible" non-code contributions (research, Miro user flows, prompt engineering, system design, and pitch preparation):
- [Arnav Bisht](team/arnav-bisht.md) — Full-Stack Architecture, DevOps/Docker, Domain Boundaries, Backend Security (PBKDF2), Auth & RBAC.
- [Diwakar Ujjwal](team/diwakar-ujjwal.md) — Frontend UX Architecture, Viewport Scroll Physics, Zero-Shift Tabs, Dynamic Navigation & Footer.
- [Aarna](team/aarna605.md) — UI/UX Design System, Muted Rose Palette Tokens, Aspect-Ratio Media Integrity, AI Assistant Widget.
- [Ravish Kansal](team/ravish-kansal.md) — Frontend UI Implementation, Landing Page Layout Assembly, Responsive Testing & QA.

---

### 4. 🏛️ Architecture & Standards
- [architecture.md](architecture.md) — System architecture diagram, responsibilities table, 17 database models schema, and mandatory operational guidelines for AI agents.
- [domain-boundaries.md](domain-boundaries.md) — Modular monolith domain boundaries (`backend/app/modules/`) and LMS data ownership principles.
- [development.md](development.md) — Quick start runbook, local environment setup, verification tests, and database management.
- [adr/](adr/) — Architectural Decision Records:
  - [`0001-modular-monolith-and-ai-boundary.md`](adr/0001-modular-monolith-and-ai-boundary.md)
  - [`0002-backend-owns-lms-data.md`](adr/0002-backend-owns-lms-data.md)

---

## 📌 Rules for AI Coding Agents
AI coding agents working in this repository must consult [architecture.md](architecture.md) and the relevant [features/](features/) document before introducing architectural modifications, schema changes, or UI adjustments.
