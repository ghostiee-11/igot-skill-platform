# Development and operations

The active local runtime is the service stack defined in `infra/compose/docker-compose.yml`. Use [LOCAL_SETUP.md](../LOCAL_SETUP.md) as the command reference and [Docker runtime operations](operations/docker-local.md) for images, startup order, health, storage and troubleshooting.

## Daily workflow

1. Read [HANDOFF.md](HANDOFF.md) for current branch/work, executed evidence and remaining issues.
2. Start Docker Desktop with Linux containers.
3. From repository root, run `powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1` for sequential image builds and startup. Use `-SkipBuild` when current images are already built.
4. Work in the owning application/service. Follow [service architecture](architecture/service-architecture.md), [service ownership](services/README.md), and more specific `AGENTS.md` files.
5. Validate the changed components using locked dependencies; update [changelog](changelog.md), handoff and relevant contracts/specs.

The helper stops services while building and preserves PostgreSQL/RabbitMQ volumes. For host frontend development, keep the gateway/services in Compose and use the root npm workspace commands in [local setup](../LOCAL_SETUP.md). Python APIs continue to require their owned PostgreSQL migrations/configuration.

## Verification

- Python services, gateway and migration tooling: install from each `uv.lock` with the documented extra, then run `uv run --frozen python -m pytest -q` in that directory. Module invocation also works for the migration utility's root `migrate.py` import.
- Frontend: TypeScript check and production webpack build. ESLint is currently a recorded, non-blocking CI baseline; its failures remain tracked in [known issues](known-issues.md).
- Compose: validate configuration, wait for health, then exercise authenticated operations through the public gateway.
- Live smoke: `uv run --project services/assessment --frozen python scripts/smoke-local.py` from root, on the bootstrapped local demo stack. It creates separate test learners/activity and temporary lab containers.
- Contract fixtures: `python scripts/validate-contracts.py`.

[Executed local runtime verification](local-runtime-2026-10-04.md) records actual results and their limits. A healthy process does not prove a configured model provider, end-to-end interoperability, durable recovery or production readiness.

## Data and configuration

The runtime uses six owned PostgreSQL schemas with separate roles, two named infrastructure volumes and an ignored local artifact directory. `local-seed` is an explicit development job, separate from Alembic and from legacy data migration. It inserts the authored local catalogue and optional demo personas; it does not fabricate progress or certificates. Preserve an existing `.env` instead of recopying defaults over it. [Bootstrap provenance](../infra/seed/README.md) and [migration ownership](migration/data-ownership.md) explain their separate scopes.

Provider keys belong in ignored local environment files. Live AI/speech features need configured providers; password recovery and semantic indexing remain unavailable. Never add credentials or runtime learner artifacts to Git.

## Historical references

The [original monolith development guide](history/development-monolith.md), [monolith architecture](architecture.md), [domain boundaries](domain-boundaries.md) and [original ADRs](adr/) remain reference material. Their backend/SQLite/Supabase commands are not the service-stack startup path. Source and current runbooks take precedence over historical feature completion claims.
