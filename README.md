# iGOT Skill Platform

Civil-service learning, assessment and competency intelligence, organized as independently deployable domain services.

This branch is rebuilding the service architecture. The existing frontend has been relocated intact; its redesign is a separate project. See the [migration status](docs/migration/status.md) for what has actually been verified.

## Repository

| Directory | Purpose |
|---|---|
| `apps/frontend/` | Existing Next.js application, preserved during backend migration |
| `apps/gateway/` | Public API entry point and compatibility with existing frontend routes |
| `services/` | Identity, learning, assessment, competency, AI, content and lab control |
| `contracts/` | Versioned service HTTP/event contracts and integration fixtures |
| `packages/` | Small shared infrastructure packages and generated API client |
| `environments/labs/` | Disposable workspace/target images and exercise manifests |
| `infra/` | Local orchestration, PostgreSQL role/schema bootstrap and messaging |
| `migrations/legacy/` | Explicit source-to-service migration and reconciliation tooling |
| `docs/` | Architecture, ownership, decisions, runbooks and migration evidence |

The old `backend/`, `content-pipeline/` and `supabase/` remain migration references until replacement behavior and data reconciliation are verified. They are not dependencies of the new services.

## Architecture

- Services own their APIs, dependencies, tests and migrations.
- Stateful services own separate PostgreSQL schemas and roles. AI and the gateway do not get domain databases.
- One assessment service hosts extensible statistical, behavioural, technical and digital-governance engines.
- Services communicate through APIs/events, never shared ORM models or cross-schema queries.
- Lab control is separate from learner execution. Local containers come first; cloud VM labs are a documented later phase.
- Application imports do not migrate or seed databases.

## Start here

- [Local setup](LOCAL_SETUP.md)
- [Documentation index](docs/README.md)
- [Architecture](docs/architecture/service-architecture.md)
- [Service ownership](docs/services/README.md)
- [Migration and verification](docs/migration/status.md)
- [Data ownership and rollback](docs/migration/data-ownership.md)
- [Known issues](docs/known-issues.md)

## Branch workflow

The `final-final` baseline was merged into `main` at `7123bd3`. Changes in this rebuild stay on `rebuild/service-architecture` until user review. Data cutover and the rebuild merge are separate actions; neither happens as a side effect of local setup.
