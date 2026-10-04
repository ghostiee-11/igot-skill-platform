# Assessment service

Owns: Course exams, generated quizzes, specialist engine sessions, grading and results.

A shared registry hosts statistical, behavioural, technical and digital-governance engines. Definitions and answer keys are server-owned. AI output is a proposal; labs return execution observations.

## Boundaries

- HTTP: `/v1`, development port `8103`.
- Database: owned PostgreSQL schema `assessment`; migrations belong here.
- Source: `src/igot_assessment`; no imports from the old backend or another service implementation.
- Verification: service-local `tests/`; cross-service checks are separate.
- Migration coverage: [status](../../docs/migration/status.md), [API inventory](../../docs/migration/api-compatibility.md), [data ownership](../../docs/migration/data-ownership.md).

## Development

Install this service from its own directory/environment using its `pyproject.toml`. Once dependencies are installed:

```sh
python -m uvicorn igot_assessment.main:app --host 127.0.0.1 --port 8103
python -m pytest tests
```

Use the service's `.env.example` to set process environment explicitly. Do not inherit the old root `.env` automatically. A database-backed endpoint requires explicit migration first; health alone is not proof the schema is ready.

See [local setup](../../LOCAL_SETUP.md) for workspace orchestration and [architecture](../../docs/architecture/service-architecture.md) for contracts. Implementation status is recorded honestly in the migration status page rather than inferred from this service's presence.

## Local event delivery

Compose runs `python -m igot_assessment.dispatch_events` as `assessment-events` from the same image. It reads assessment-owned pending outbox records, sends course outcomes to learning and evidence to competency through authenticated idempotent HTTP APIs, and records `published_at` only after delivery succeeds. Failures remain pending and are retried. This local transport is HTTP; RabbitMQ assessment event publishers/consumers are still planned.
