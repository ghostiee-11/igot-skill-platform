# LMS domain boundaries

> Historical monolith boundaries. For the rebuild use the [service catalogue](services/README.md), [architecture](architecture/service-architecture.md) and [data map](migration/data-ownership.md).

The backend is organized as a modular monolith under `backend/app/modules`. This
change moves existing routers and request schemas; it does not introduce new
business behavior.

- `auth` owns login, registration, password-reset responses, and identity lookup.
- `onboarding` and `profile` own learner-supplied profile information.
- `discover` and `courses` own catalogue queries, course details, and enrollment.
- `learning` owns the lesson player, practice activity checks, and progress updates.
- `assessments` owns assessment delivery, submission, scoring, and completion effects.
- `dashboard` assembles the existing learner dashboard read model.
- `admin` owns the existing administrator overview, assignment, and course-creation endpoints.
- `agents` remains outside the LMS domain modules until the planned AI extraction is designed and implemented.

SQLAlchemy models remain centralized in `backend/app/models` because separating the
database model is a future design decision, not part of this mechanical move. Core
configuration, database setup, security, and seed data remain in `backend/app/core`.

Modules may gain services or repositories when real behavior requires them. Empty
layer directories are intentionally not included.
