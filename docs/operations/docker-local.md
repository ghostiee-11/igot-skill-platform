# Local Docker runtime

Runtime: `infra/compose/docker-compose.yml`. Current source developed on `rebuild/lms`, targeting `main` through the authorized pull request. Baseline before this work: `0d0f6d2` on `main`.

## Images and processes

| Compose service | Image source | Expected successful state | Purpose |
|---|---|---|---|
| `postgres` | `postgres:16-bookworm` | Healthy | Local PostgreSQL database and six owned schemas |
| `rabbitmq` | `rabbitmq:4-management` | Healthy | Content task broker and management UI |
| `identity` | `services/identity/Dockerfile` | Healthy | Authentication, roles, profiles and onboarding |
| `learning` | `services/learning/Dockerfile` | Healthy | Catalogue, lessons, progress, completion and certificates |
| `assessment` | `services/assessment/Dockerfile` | Healthy | Exams, specialist/interview sessions and grading |
| `competency` | `services/competency/Dockerfile` | Healthy | Taxonomy, evidence, gap analysis and recommendations |
| `ai` | `services/ai/Dockerfile` | Healthy process | Provider generation and fallback assistant; readiness may be degraded |
| `content` | `services/content/Dockerfile` | Healthy | Uploaded/text extraction, sources, transcripts and jobs |
| `labs` | `services/labs/Dockerfile` | Healthy | Local execution controller and notebook proxy |
| `gateway` | `apps/gateway/Dockerfile` | Healthy | Public `/api` compatibility routes and aggregation |
| `frontend` | `apps/frontend/Dockerfile` | Healthy | Next.js standalone frontend on port 3000 |
| `assessment-events` | Shares assessment image | Running | Retries outbox delivery through idempotent HTTP APIs |
| `content-worker` | Shares content image | Running | Consumes RabbitMQ source jobs, concurrency one |
| `local-seed` | Shares assessment image; mounts `infra/seed/` read-only | Exited (0) | Explicit local catalogue/demo bootstrap |
| `lab-workspace-image` | `environments/labs/workspace/Dockerfile` | Exited (0) | Builds/checks the allowlisted Marimo runtime image |
| `lab-target-demo-image` | `environments/labs/targets/demo/Dockerfile` | Exited (0) | Builds/checks the allowlisted demonstration target |

Python images use Python 3.12 and frozen `uv.lock` dependencies. Frontend uses Node 22 Bookworm, bounded webpack build memory/two page workers, and a non-root standalone runtime containing traced server dependencies, static bundles and public assets. Only `NEXT_PUBLIC_API_URL` is a frontend build argument; private provider keys are not frontend build inputs. The browser-facing local API value is `http://localhost:8000/api`.

## Startup order

1. PostgreSQL initializes development schema roles on a new named volume; RabbitMQ starts.
2. Stateful APIs apply their owned Alembic migrations before starting. Infrastructure health gates the APIs.
3. Lab runtime one-shot containers complete before the labs controller starts. Labs readiness checks its database and Docker socket.
4. `local-seed` runs after identity/learning/assessment/competency health. Gateway waits for upstream health and successful seed exit.
5. Assessment dispatcher/content worker start after their owning API/dependencies; frontend waits for gateway health.

Bootstrap and migrations have different jobs. Alembic owns schema changes; local seed owns the optional authored demo catalogue; `migrations/legacy` imports historical data only through an explicit reviewed command. Set `LOCAL_DEMO_SEED_ENABLED=false` for a custom/imported environment. Matching existing rows and credentials are preserved; conflicting fixture identifiers fail rather than attaching lessons to unrelated data. See [seed provenance](../../infra/seed/README.md).

## Commands

Run from repository root. See [LOCAL_SETUP.md](../../LOCAL_SETUP.md) for complete commands and environment values.

```powershell
# Build sequentially, then start and wait; stops existing services during build.
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1

# Start current images without rebuilding.
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -SkipBuild

# Inspect every container, including successful one-shot jobs.
docker compose --env-file .env -f infra/compose/docker-compose.yml ps -a

# Stop/release containers while keeping infrastructure data.
docker compose --env-file .env -f infra/compose/docker-compose.yml down
```

Compose `--build` startup is also supported. Sequential builds reduce memory spikes on Windows; they are not a requirement to rename the project or recreate databases. The helper never modifies Docker Desktop/WSL configuration automatically.

## Persistent state

- Named volumes: `igot-skill-platform_postgres-data`, `igot-skill-platform_rabbitmq-data`.
- Host artifact bind mount: `infra/storage/artifacts/` to `/var/lib/igot/artifacts` in content/worker/labs; generated files are ignored by Git.
- Lab execution: separately labelled disposable networks/containers managed by labs; verify cleanup with the `igot.lab.session` label. Scheduled expiry reconciliation remains pending, so stop unused sessions through the application.
- Environment: ignored root `.env`, preserved by the startup helper. Local signing/database/demo defaults are development values; changing initialization passwords does not retroactively update an existing PostgreSQL volume.

Normal image rebuilds/restarts do not erase named volumes. A schema-role bootstrap script runs only when PostgreSQL initializes a new database volume; an older custom volume may need an explicit role/schema repair. Diagnose its logs before changing anything. Avoid `down --volumes`, prune-volume commands and Desktop factory reset during normal recovery.

## Failure diagnosis

| Symptom | Check / repair boundary |
|---|---|
| Docker CLI cannot reach its engine | Check Desktop Linux-container mode and engine availability before inspecting application code |
| Desktop error at `dockerInference` or `engine.sock` | Host AF_UNIX runtime socket failure; preserve/recreate only the stopped Desktop temporary runtime parent directories as described in local setup |
| Build/download `unexpected EOF` | Inspect Desktop and Windows resource-exhaustion logs; use sequential builds and a host-appropriate WSL memory/swap limit |
| API exits immediately with no logs | Validate image launch files; zero-byte uvicorn/Alembic scripts were found in an interrupted content image on this host; rebuild the affected image without cache |
| API migration error | Inspect owned service/database logs and migration version; do not reset volumes blindly |
| Seed exits nonzero | Read its conflict/schema error; choose explicit migration or disable local demo seeding for custom data |
| Web job stays queued | Check `content-worker`, RabbitMQ connection and queue consumers; control/event subscription queues are exclusive for RabbitMQ 4 compatibility |
| Exam passes but completion/certificate is absent | Check `assessment-events`, pending assessment outbox rows and learning migration `0002_certificate_attempt_ids` |
| AI `/v1/ready` is degraded | No live provider is configured; process health and deterministic fallback are still available |

The 2026-10-04 host originally permitted 12 GB WSL RAM on a 16 GB machine with a fixed 4 GB Windows pagefile. Confirmed resource-exhaustion events stopped Docker during builds. Its original WSL config was backed up and the running VM was capped at 2 GB with existing 8 GB swap. This is a machine-specific recovery choice, not the repository's universal RAM requirement. Docker socket recovery retained images/volumes; no factory reset was used. See [executed receipt](../local-runtime-2026-10-04.md).

## Verification and boundaries

Eleven containers have health checks; the two background workers are process-supervised, not HTTP-health-checked. The gateway readiness endpoint checks its process, while Compose's initial dependency gates check upstream health. Use actual gateway smoke journeys to validate behavior after startup.

Current verification includes learner login/enrolment/player, assessment/certificate persistence, adaptive questions, isolated technical grading, cyber HTTP ingress, quiz/interview fallbacks and a RabbitMQ extraction job. It does not establish production sandbox authorization, full WebSocket/browser exam coverage, live provider behavior without keys, or legacy cutover correctness. Local labs mount the Docker socket; use [lab operations](labs.md) before shared deployment.
