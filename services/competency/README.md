# Competency service

Owns: Taxonomy, evidence, mappings, target levels, gaps, recommendations and competency analytics.

Evidence is traceable and idempotently accepted. Historical results retain provenance. Learning owns course records; this service obtains candidates through a contract or an explicitly owned projection.

## Boundaries

- HTTP: `/v1`, development port `8104`.
- Database: owned PostgreSQL schema `competency`; migrations belong here.
- Source: `src/igot_competency`; no imports from the old backend or another service implementation.
- Verification: service-local `tests/`; cross-service checks are separate.
- Migration coverage: [status](../../docs/migration/status.md), [API inventory](../../docs/migration/api-compatibility.md), [data ownership](../../docs/migration/data-ownership.md).

## Development

Install this service from its own directory/environment using its `pyproject.toml`. Once dependencies are installed:

```sh
python -m uvicorn igot_competency.main:app --host 127.0.0.1 --port 8104
python -m pytest tests
```

Use the service's `.env.example` to set process environment explicitly. Do not inherit the old root `.env` automatically. A database-backed endpoint requires explicit migration first; health alone is not proof the schema is ready.

See [local setup](../../LOCAL_SETUP.md) for workspace orchestration and [architecture](../../docs/architecture/service-architecture.md) for contracts. Implementation status is recorded honestly in the migration status page rather than inferred from this service's presence.
