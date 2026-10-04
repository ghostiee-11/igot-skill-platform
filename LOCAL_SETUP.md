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
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
docker compose --env-file .env -f infra/compose/docker-compose.yml up -d --build --wait --wait-timeout 240
```

On Windows hosts with limited available memory, use the sequential build/start helper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

This stops the local services while rebuilding images one at a time, retains all volumes, and waits for startup health. After the first successful build, start without rebuilding:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -SkipBuild
```

The copied environment file contains development-only defaults. Replace its signing secrets before sharing an environment. AI keys are optional; the AI service uses deterministic fallback behavior when no provider is configured.

Compose waits for PostgreSQL and RabbitMQ, then each stateful service runs its Alembic migration before starting. A separate `local-seed` job inserts the branch's authored four-course catalogue, lessons, exams, competency taxonomy and lab definitions before the gateway starts. It does not import legacy learner history or fabricate completions. Repeated starts preserve existing matching records; conflicting catalogue identifiers fail explicitly. Set `LOCAL_DEMO_SEED_ENABLED=false` to disable this local bootstrap. See `infra/seed/README.md` for provenance.

The `assessment-events` process retries committed assessment events through the learning and competency services' idempotent HTTP APIs. Passing course exams therefore produces durable completion and certificate records. This is an outbox-backed HTTP dispatcher; RabbitMQ event publishers/consumers remain separate future work.

The `content-worker` process consumes source-processing jobs from RabbitMQ with one worker process, so accepted web-extraction jobs can finish.

The local Compose configuration enables the frontend's standard learner quick login:

- Email: `rajesh.kumar@mospi.gov.in`
- Password: `Learner@123`

The separate local bootstrap also provisions the login screen's Admin and New Onboard personas when `DEMO_ACCOUNTS_ENABLED=true`. Existing account credentials and onboarding records are preserved.

Identity creates or repairs this learner when those exact credentials are used, so it survives database resets and incomplete demo imports. Set `DEMO_ACCOUNTS_ENABLED=false` outside local/demo environments.

## Verify the stack

| Component | URL |
|---|---|
| Frontend | <http://localhost:3000> |
| Public gateway | <http://localhost:8000> |
| Gateway health | <http://localhost:8000/health> |
| Gateway OpenAPI | <http://localhost:8000/openapi.json> (gateway metadata; proxy operations are not expanded here) |
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
| Labs | <http://localhost:8107/v1/health> |

Assessment/content/labs readiness adds database/runtime checks at `/v1/ready`. AI `/v1/ready` reports `degraded` with no live provider keys even while `/v1/health` and the fallback assistant work. Gateway `/ready` is a process-level check; Compose startup gates it on upstream health. The two workers have no separate HTTP health endpoint. The lab-image and `local-seed` one-shot containers should show `Exited (0)` after successful startup, not remain running.

Inspect startup and migration failures with:

```powershell
docker compose --env-file .env -f infra/compose/docker-compose.yml ps -a
docker compose --env-file .env -f infra/compose/docker-compose.yml logs --tail 100 gateway identity learning assessment competency ai content labs local-seed assessment-events content-worker
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
uv run --frozen python -m pytest -q
```

Use `--extra dev` instead of `--extra test` for `apps/gateway`. Each service reads its own environment variables and still requires PostgreSQL and RabbitMQ where applicable.

Run the frontend locally:

```powershell
npm ci
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000/api"
npm --workspace apps/frontend run dev
```

Run these frontend commands from the repository root. The reproducible production build used by Docker is `npm --workspace apps/frontend run build -- --webpack`. Typecheck with `node node_modules/typescript/bin/tsc --noEmit -p apps/frontend/tsconfig.json`. If Windows locks `.next/trace`, stop the relevant Next.js process or validate through the clean frontend Docker build.

Service CI uses `uv run --frozen python -m pytest -q` in each service/gateway/migration directory. Gateway dependencies use the `dev` extra; all seven services and legacy migration tooling use `test`. To exercise the running stack:

```powershell
uv run --project services/assessment --frozen python scripts/smoke-local.py
```

This smoke check creates separate local test learners and activity, uses the checked-in local fixture answer keys to verify grading, starts/terminates temporary lab containers, and checks certificates through the gateway. It assumes the local bootstrap catalogue is present; use it on a local demo stack, not an imported production environment.

The frontend Docker image uses the Next.js standalone server with static/public assets and a non-root user. Its webpack build uses bounded Node memory and two page-generation workers.

## Docker Desktop socket errors on Windows

For the separation between repository configuration, host-specific recovery and data migration, see [Docker runtime and troubleshooting](docs/operations/docker-local.md).

An error containing `initializing Inference manager` / `dockerInference` or `initializing Secrets Engine` / `engine.sock` can prevent Docker itself from starting. These are Docker Desktop host runtime sockets, not application images. On the audited Windows host, individual sockets were inaccessible even after Docker stopped. Preserving and renaming their parent runtime directories allowed Docker to recreate them, with images and volumes retained.

Stop Docker using `docker desktop stop --force --timeout 20` first. Verify no Docker Desktop/backend process remains, then preserve the affected runtime directory under a unique name (`%LOCALAPPDATA%/Docker/run` or `%LOCALAPPDATA%/docker-secrets-engine`) and restart Docker Desktop. Do not rename or delete its `wsl` data directory. See [Docker's matching issue report](https://github.com/docker/desktop-feedback/issues/554). A Windows restart may be needed if runtime directories remain inaccessible.

Separate `unexpected EOF` build failures on this host correlated with Windows Resource-Exhaustion-Detector low-virtual-memory events. Its Windows paging file is fixed at 4 GB. WSL's previous 12 GB limit was backed up and lowered to 2 GB with 8 GB swap; a full WSL shutdown was needed to apply the limit. Avoid parallel builds and keep the stack stopped while compiling on this host. No Windows reboot, factory reset or volume removal was performed.

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
- Password recovery and semantic vector indexing return unavailable responses; keys alone do not implement those integrations. Live AI generation and speech need their corresponding provider keys. See [verification and limits](docs/local-runtime-2026-10-04.md).
