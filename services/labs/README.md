# Labs service

Owns: Runtime sessions, browser access, execution records, expiry, reset and cleanup.

Runtime control and learner execution are separate. Learner containers receive no application credentials or Docker socket. No host subprocess fallback. Cloud VM implementation is deferred.

## Boundaries

- HTTP: `/v1`, development port `8107`.
- Database: owned PostgreSQL schema `labs`; migrations belong here.
- Source: `src/igot_labs`; no imports from the old backend or another service implementation.
- Verification: service-local `tests/`; cross-service checks are separate.
- Migration coverage: [status](../../docs/migration/status.md), [API inventory](../../docs/migration/api-compatibility.md), [data ownership](../../docs/migration/data-ownership.md).

## Development

Install this service from its own directory/environment using its `pyproject.toml`. Once dependencies are installed:

```sh
python -m uvicorn igot_labs.main:app --host 127.0.0.1 --port 8107
python -m pytest tests
```

Use the service's `.env.example` to set process environment explicitly. Do not inherit the old root `.env` automatically. A database-backed endpoint requires explicit migration first; health alone is not proof the schema is ready.

See [local setup](../../LOCAL_SETUP.md) for workspace orchestration and [architecture](../../docs/architecture/service-architecture.md) for contracts. Implementation status is recorded honestly in the migration status page rather than inferred from this service's presence.
