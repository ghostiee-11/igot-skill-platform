# iGOT Skill Platform

Civil-service learning, assessment and competency intelligence, organized as independently deployable domain services.

The local runtime is the service stack in `infra/compose/docker-compose.yml`: Next.js frontend, public gateway, seven domain services, PostgreSQL, RabbitMQ and background workers. LMS work was developed on `rebuild/lms`. See [current verification](docs/local-runtime-2026-10-04.md) for executed checks and [known issues](docs/known-issues.md) for remaining limitations.

## Run locally

With Docker Desktop running Linux containers, start from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

The helper creates `.env` only if absent, validates Compose, builds one image at a time, runs migrations and local bootstrap, and waits for startup. It stops existing services during builds and preserves their volumes. Open [the frontend](http://localhost:3000). Subsequent starts can use `scripts/start-local.ps1 -SkipBuild`.

Use [LOCAL_SETUP.md](LOCAL_SETUP.md) for platform-independent Compose commands, provider configuration, testing and stop/recovery operations. The [Docker runtime guide](docs/operations/docker-local.md) explains images, workers, storage and expected container states. Local health does not imply that live providers or every specialist feature are enabled.

## Repository

| Directory | Purpose |
|---|---|
| `apps/frontend/` | Next.js learner/admin application and standalone frontend Docker image |
| `apps/gateway/` | Public API entry point and compatibility with existing frontend routes |
| `services/` | Identity, learning, assessment, competency, AI, content and lab control |
| `contracts/` | Versioned service HTTP/event contracts and integration fixtures |
| `packages/` | Small shared infrastructure packages and generated API client |
| `environments/labs/` | Disposable workspace/target images and exercise manifests |
| `infra/` | Compose, PostgreSQL role/schema bootstrap, explicit local fixtures and artifact storage |
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

The pre-LMS `main` baseline is commit `0d0f6d2` (the earlier service-architecture PR merge). `rebuild/lms` adds LMS changes and documented local-runtime repairs on top of that baseline. [PR #2](https://github.com/ghostiee-11/igot-skill-platform/pull/2) is the authoritative integration/check/merge record; [HANDOFF.md](docs/HANDOFF.md) contains continuity and verification details. Code merging does not import legacy learner data, reset Docker volumes or authorize production cutover.
