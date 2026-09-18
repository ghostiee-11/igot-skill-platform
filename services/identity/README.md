# Identity service

Owns: Accounts, credentials, roles, profile editing, onboarding and departments.

Public registration creates learners. Identity alone verifies passwords and issues user tokens. Service consumers use the identity contract rather than reading identity tables.

The optional `DEMO_ACCOUNTS_ENABLED` mode guarantees the configured learner quick login by creating or repairing that learner only when the exact configured email/password pair is submitted. It is enabled by local Compose and disabled by the standalone service default; do not enable it in production.

## Boundaries

- HTTP: `/v1`, development port `8101`.
- Database: owned PostgreSQL schema `identity`; migrations belong here.
- Source: `src/igot_identity`; no imports from the old backend or another service implementation.
- Verification: service-local `tests/`; cross-service checks are separate.
- Migration coverage: [status](../../docs/migration/status.md), [API inventory](../../docs/migration/api-compatibility.md), [data ownership](../../docs/migration/data-ownership.md).

## Development

Install this service from its own directory/environment using its `pyproject.toml`. Once dependencies are installed:

```sh
python -m uvicorn igot_identity.main:app --host 127.0.0.1 --port 8101
python -m pytest tests
```

Use the service's `.env.example` to set process environment explicitly. Do not inherit the old root `.env` automatically. A database-backed endpoint requires explicit migration first; health alone is not proof the schema is ready.

See [local setup](../../LOCAL_SETUP.md) for workspace orchestration and [architecture](../../docs/architecture/service-architecture.md) for contracts. Implementation status is recorded honestly in the migration status page rather than inferred from this service's presence.
