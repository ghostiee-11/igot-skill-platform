# Ai service

Owns: Provider access, generation, assistant orchestration and provider-backed speech capabilities.

This service has no LMS database. It receives request-scoped context and returns outputs/provenance. It cannot award credentials, mutate learner progress or bypass domain authorization.

## Boundaries

- HTTP: `/v1`, development port `8105`.
- Database: none; stateless domain adapter.
- Source: `src/igot_ai`; no imports from the old backend or another service implementation.
- Verification: service-local `tests/`; cross-service checks are separate.
- Migration coverage: [status](../../docs/migration/status.md), [API inventory](../../docs/migration/api-compatibility.md), [data ownership](../../docs/migration/data-ownership.md).

## Development

Install this service from its own directory/environment using its `pyproject.toml`. Once dependencies are installed:

```sh
python -m uvicorn igot_ai.main:app --host 127.0.0.1 --port 8105
python -m pytest tests
```

Use the service's `.env.example` to set process environment explicitly. Do not inherit the old root `.env` automatically. A database-backed endpoint requires explicit migration first; health alone is not proof the schema is ready.

See [local setup](../../LOCAL_SETUP.md) for workspace orchestration and [architecture](../../docs/architecture/service-architecture.md) for contracts. Implementation status is recorded honestly in the migration status page rather than inferred from this service's presence.
