# Feature Catalog & Specifications

> Original platform specifications. Use the [migration catalogue](service-migration-catalogue.md) for new ownership and [migration status](../migration/status.md) for verified coverage. Old paths and completion claims are historical until revalidated.

This directory contains comprehensive, feature-level architectural and functional specifications for the **iGOT Karmayogi (MoSPI)** platform.

Each document provides deep technical context designed for **human developers** and **autonomous AI coding agents** to understand domain boundaries, user flows, database models, frontend components, API endpoints, and critical implementation constraints.

---

## Feature Catalog

| Feature Specification | Status | Primary Modules / Routes | Key Models / Entities |
|---|---|---|---|
| [AI Copilot](ai-copilot.md) | **Implemented** (Phase 0) | `backend/app/agents/`, `/api/agents/chat`, `AiAssistantWidget.tsx` | LangGraph StateGraph, Gemini / OpenAI / MoSPI Fallback Engine |
| [Course Management](course-management.md) | **Implemented** (Phase 0) | `/discover`, `/courses/[id]`, `/learn/[courseId]` | `Course`, `Module`, `Lesson`, `Enrollment`, `Progress` |
| [Assessment & Certification](assessment-certification.md) | **Implemented** (Phase 0) | `/assess/[assessmentId]`, `CertificateModal.tsx` | `Assessment`, `Question`, `AssessmentAttempt`, Certificates |
| [Auth, RBAC & Onboarding](auth-rbac.md) | **Implemented** (Phase 0) | `/login`, `/register`, `/onboarding`, `backend/app/modules/auth` | `User`, `UserProfile`, `Department`, PBKDF2-HMAC, Test Personas |
| [Analytics & Dashboards](analytics-dashboard.md) | **Implemented** (Phase 0) | `/home`, `/admin`, `/my-learning`, `backend/app/modules/dashboard` | `LearningHistory`, `SearchHistory`, `UserSkill`, `Skill` |
| [UI/UX Design System](ui-design-system.md) | **Implemented** (Phase 0) | Global tokens, `Navbar.tsx`, `Footer.tsx`, `globals.css` | Navy Blue & Gold standard, Slate neutral, Viewport-snap scroll |
| [Homepage & Public Portal](homepage-portal.md) | **Implemented** (Phase 0) | Landing page (`/`), `EntryLandingPage.tsx` | 5-section layout, Navy/Gold palette, connected timeline, stats |

---

## Guidelines for Adding or Updating Features

When authoring a new feature document:
1. Copy the structure from [`_template.md`](_template.md).
2. Explicitly specify the **User Flow**, **Frontend Components**, **Backend API Endpoints**, and **SQLAlchemy Models**.
3. Detail any **Rules & Constraints for AI Agents** (e.g. error handling fallbacks, styling tokens, security rules).
4. Cross-link related documentation and update this `README.md` table.
