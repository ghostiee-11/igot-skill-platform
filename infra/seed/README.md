# Local catalogue bootstrap

`local-seed` is an explicit one-shot Compose job after database migrations and before gateway startup. It uses a read-only JSON fixture and separate schema-owned database roles. Runtime applications do not import historical backend code.

The fixture was exported from the authored content on `rebuild/lms`: `backend/app/core/seed_data.py` (course definitions and current `sync_course_curriculum_videos` curriculum), digital-governance course exam and pure challenge generators, technical lab templates, competency taxonomy/mapping and price-statistics question templates. It includes four courses, 12 modules, 27 lessons, three course exams with 21 questions, six technical labs, six cyber challenges, nine adaptive statistical items, four domains and 35 competencies. It contains no accounts, learner activity or provider credentials. Training challenge flags are answer keys, not system credentials.

Course outcomes use the nine authored skill definitions/links from the course seeds, independently of the broader competency taxonomy.

Regenerate explicitly from the repository root:

```powershell
services/assessment/.venv/Scripts/python.exe scripts/export-local-fixtures.py
```

Review fixture changes before using them. The exporter reads seed constructors and invokes pure content generators; it bypasses legacy database package initializers. The generated JSON is versioned so container startup requires neither historical Python dependencies nor the absent `backend/karmayogi.db`.

`seed.py` inserts missing catalogue records, checks existing identifiers against catalogue identity and updates PostgreSQL sequences. It never overwrites catalogue rows, credentials or learner history. A mismatch fails the bootstrap rather than joining fixture lessons or questions to unrelated data. Use `LOCAL_DEMO_SEED_ENABLED=false` for an imported/custom environment. This bootstrap is for local development and does not replace a reviewed production migration.

With `DEMO_ACCOUNTS_ENABLED=true`, a separate step provisions the three existing login-screen personas using local Compose environment values, preserving any existing credentials and onboarding profiles. It refreshes learning's identity read-model snapshots under separate schema roles. Account data and hashes are generated at startup and are absent from the versioned fixture.
