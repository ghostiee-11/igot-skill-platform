# Local development

This runbook starts the service-based platform defined in `infra/compose/docker-compose.yml`. The old `backend/run.py`, SQLite and Supabase instructions are migration references, not the active local runtime.

## Prerequisites

- Docker Desktop with Linux containers and Compose v2
- Git
- Node.js 22 only if you want to run the frontend outside Docker
- Python 3.12 and `uv` only if you want to run or test Python services outside Docker

## Start the standard stack

Set `SARVAM_API_KEY` in the root `.env` file to enable the live interview's **Dictate answer** speech-to-text control.

From the repository root:

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infra/compose/docker-compose.yml up -d --build
```

The copied environment file contains development-only defaults. Replace its signing secrets before sharing an environment. AI keys are optional; the AI service uses deterministic fallback behavior when no provider is configured.

Compose waits for PostgreSQL and RabbitMQ, then each stateful service runs its Alembic migration before starting. It does not import legacy data or seed demonstration accounts automatically.

The local Compose configuration enables the frontend's standard learner quick login:

- Email: `rajesh.kumar@mospi.gov.in`
- Password: `Learner@123`

Identity creates or repairs this learner when those exact credentials are used, so it survives database resets and incomplete demo imports. Set `DEMO_ACCOUNTS_ENABLED=false` outside local/demo environments.

## Verify the stack

| Component | URL |
|---|---|
| Frontend | <http://localhost:3000> |
| Public gateway | <http://localhost:8000> |
| Gateway health | <http://localhost:8000/health> |
| Gateway OpenAPI | <http://localhost:8000/openapi.json> |
| RabbitMQ management | <http://localhost:15672> |

Service health endpoints are available directly during development:

| Service | Health URL |
|---|---|
| Identity | <http://localhost:8101/health> |
| Learning | <http://localhost:8102/health> |
| Assessment | <http://localhost:8103/v1/health> |
| Competency | <http://localhost:8104/health> |
| AI | <http://localhost:8105/v1/health> |
| Content | <http://localhost:8106/v1/health> |

Inspect startup and migration failures with:

```powershell
docker compose --env-file .env -f infra/compose/docker-compose.yml ps
docker compose --env-file .env -f infra/compose/docker-compose.yml logs --tail 200 gateway identity learning assessment competency ai content
```

## Local labs

The standard Compose command builds the two allowlisted runtime images and starts the labs controller with the rest of the platform. The controller mounts the local Docker socket, so this all-in-one topology is for local development only.

Verify both the labs database and Docker runtime:

```powershell
Invoke-RestMethod http://localhost:8107/v1/ready
```

The local target is a lifecycle/isolation demonstration, not an intentionally vulnerable environment. See `docs/operations/labs.md` for the security boundary.

## Run components outside Docker

Install a Python service from its lockfile and run its tests from that service directory:

```powershell
cd services/identity
uv sync --frozen --extra test
uv run --frozen pytest -q
```

Use `--extra dev` instead of `--extra test` for `apps/gateway`. Each service reads its own environment variables and still requires PostgreSQL and RabbitMQ where applicable.

Run the frontend locally:

```powershell
cd apps/frontend
npm ci
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000/api"
npm run dev
```

The production build command is `npm run build`. If Windows locks `.next/trace`, stop any running Next.js process or validate through the clean frontend Docker build.

## Legacy data

Legacy migration is always explicit; startup never reads `backend/karmayogi.db`:

```powershell
cd migrations/legacy
uv sync --frozen --extra test
uv run migrate.py --source-url sqlite:///C:/absolute/path/to/karmayogi.db
```

Read `migrations/legacy/README.md` before apply mode. Apply only to a disposable target until field-level reconciliation and rollback have been rehearsed.

## Stop or reset

Stop the standard stack while preserving PostgreSQL and RabbitMQ volumes:

```powershell
docker compose --env-file .env -f infra/compose/docker-compose.yml down
```

To erase local databases and broker state, add `--volumes`. That operation is destructive and is not required for ordinary restarts.

## Current limitations

- Several specialist compatibility endpoints remain under migration; check `docs/migration/status.md` and `docs/known-issues.md` before assuming full legacy parity.
- The copied frontend still has inherited lint debt even though its typecheck and clean container production build pass.
- Local Docker labs are not the planned cloud-VM runtime.
