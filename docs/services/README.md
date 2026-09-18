# Service catalogue

This catalogue defines ownership. See [migration status](../migration/status.md) for implemented and verified coverage.

| Deployment | Port | Schema | Owns |
|---|---:|---|---|
| Frontend | 3000 | none | Existing public, learner, assessment, lab and admin screens; copied intact |
| Gateway | 8000 | none | Public routing, legacy API compatibility, bounded aggregation |
| Identity | 8101 | `identity` | Accounts, credentials, roles, profiles, onboarding, departments |
| Learning | 8102 | `learning` | Published curriculum, enrollments, progress, assignments, certificates, learning read models |
| Assessment | 8103 | `assessment` | Exams, quizzes, attempts, specialist engines, grading and result production |
| Competency | 8104 | `competency` | Taxonomy, evidence mappings, evidence ledger, targets, scores, gaps, recommendations |
| AI | 8105 | none | Model provider calls, generation, assistant workflows and provider-backed speech adapters |
| Content | 8106 | `content` | Source resources, uploads, extraction, ingestion jobs and publication workflow |
| Labs | 8107 | `labs` | Session lifecycle, access, execution records, artifact references and cleanup |

## Responsibilities that cross services

- Profile editing belongs to identity. Certificates shown on a profile come from learning. The gateway may aggregate their responses for the existing frontend.
- Assessment owns exam definitions and attempts. Learning references them by ID; it does not query assessment tables.
- Assessment completion produces evidence and a completion event. Learning applies its completion policy and owns credential issuance. Competency interprets evidence independently.
- Statistical mastery is assessment-engine state. The corresponding standardized evidence is consumed by competency.
- Technical exercise definitions and expected outcomes belong to assessment. Labs owns only the execution environment and observations; hidden tests are never returned to the browser.
- Content owns source documents/resources. Learning owns accepted published lessons. AI returns drafts; publication is a content/learning decision.
- Admin APIs stay with the owner of each operation. A single admin screen does not imply a single service with access to everyone's tables.
- AI receives only the context required for an operation. It neither connects to LMS schemas nor becomes a second LMS datastore.

## Per-service contract

Every deployable Python service needs an installable `pyproject.toml`, reproducible dependency resolution, container image, example environment, health/readiness endpoints, owned tests and an explicit run command. Stateful services additionally own migration and seed commands. Configuration must never silently load the old repository's live `.env`.

An unavailable dependency may disable the affected operation, but should not prevent unrelated functions from serving requests. Unit tests use fakes at remote boundaries. Integration tests use PostgreSQL rather than relying on SQLite-specific behavior.
