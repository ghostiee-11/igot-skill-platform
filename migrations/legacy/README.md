# Legacy database migration

This utility inventories the monolith database and copies records into service-owned PostgreSQL schemas. It never reads the repository root `.env`; both endpoints must be explicit.

Dry run:

```powershell
uv run migrate.py --source-url sqlite:///C:/absolute/path/to/karmayogi.db
```

Disposable-target apply:

```powershell
uv run migrate.py `
  --source-url sqlite:///C:/absolute/path/to/karmayogi.db `
  --target-url postgresql+psycopg://migration_user:password@localhost:5432/igot_rehearsal `
  --apply
```

Apply mode orders parent tables before their children, decodes legacy JSON text into typed JSON columns, preserves explicit identifiers, advances PostgreSQL sequences, reports insert failures separately from existing-key skips, and compares every mapped destination count with its source.

To import only a reconciled subset into an already running local stack, pass `--only-tables modules lessons assessments questions` with the normal explicit URLs and `--apply`. The subset skips unrelated tables and does not create or populate the migration archive. Back up the target database first and verify that parent course IDs already match the source.

Exit codes are `0` for a clean run, `2` for populated unmapped/archive blockers, `3` for failed inserts and `4` for count mismatches. A clean count reconciliation does not replace field-level hash/timestamp verification or a rollback rehearsal.
