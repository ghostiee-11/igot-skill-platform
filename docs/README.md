# Documentation index

Start with the current runtime. Historical documents are retained for provenance and should not be used as today's startup or feature-completion checklist.

## Current setup and operations

| Document | Purpose |
|---|---|
| [Repository overview](../README.md) | Application layout, current runtime and branch workflow |
| [Local setup](../LOCAL_SETUP.md) | Authoritative startup, configuration, test and stop commands |
| [Docker runtime guide](operations/docker-local.md) | Image/process inventory, startup order, storage, health and recovery |
| [Handoff](HANDOFF.md) | Current work, decisions, executed evidence and next steps |
| [Executed local verification](local-runtime-2026-10-04.md) | Actual runtime checks and limitations |
| [Development workflow](development.md) | Daily contribution/testing workflow with current paths |
| [Lab operations](operations/labs.md) | Execution boundary and local lifecycle |
| [Bootstrap provenance](../infra/seed/README.md) | Authored fixture contents, repeatability and demo account behavior |
| [Known issues](known-issues.md) | Current unavailable features, lint/content debt and production limits |

## Architecture and migration

- [Service architecture](architecture/service-architecture.md): owned boundaries and current local HTTP/task delivery versus the target event transport.
- [Service catalogue](services/README.md): ports, schema ownership and background processes.
- [Architecture decisions](decisions/README.md): accepted service/lab decisions; acceptance is separate from verification.
- [Migration status](migration/status.md): current evidence plus labelled historical checks.
- [Data ownership and rollback](migration/data-ownership.md): explicit legacy migration scope and reconciliation requirements.
- [API compatibility](migration/api-compatibility.md) and [feature migration catalogue](features/service-migration-catalogue.md): interface/behavior inventory, not automatic completion claims.

## Feature and contribution references

The [feature index](features/README.md) links detailed specifications. Many original feature pages describe the monolith implementation; use the service migration catalogue, source/tests and current verification before treating them as current runtime behavior. [Changelog](changelog.md) records changes and [team logs](team/README.md) retain contribution history.

Deferred work: [frontend redesign](plans/frontend-rebuild.md) and [cloud VM labs](plans/cloud-vm-labs.md).

## Historical material

- [Original monolith development guide](history/development-monolith.md).
- [Monolith architecture](architecture.md), [module boundaries](domain-boundaries.md), and [original ADRs](adr/).
- [2026-09-23 runtime parity audit](migration/runtime-parity-audit-2026-09-23.md), including its dated repairs.
- [Initial 2026-10-04 read-only audit](local-validation-2026-10-04.md), superseded for runtime status by the executed repair receipt.

Keep historical results dated. Do not translate an old test count, SQLite example, hosted/Supabase setup or demo progress snapshot into a claim about the current service stack.

## Agent entry

Read `HANDOFF.md`, this index and `../LOCAL_SETUP.md` first, then application-specific `AGENTS.md` files. Use source, tests, migrations and actual execution to distinguish planned, implemented, tested and executed work. Keep ownership boundaries; no service implementation imports or cross-schema application queries. Update handoff/specs/changelog at meaningful milestones and before ending work. Never store credentials, provider keys or runtime learner artifacts in these documents.
