# Repository handoff

Updated: 2026-10-05 (Asia/Calcutta). Owner: primary coding agent; no delegation.

## Goal and current state

The LMS runtime was verified healthy on 2026-10-04 with all APIs, workers and bootstrap jobs working. The latest 2026-10-05 check found Docker Desktop's Linux engine unavailable; do not claim the stack is currently running until it is restarted. The documented recovery/start command preserves existing images and volumes.

Current Git workflow: PR #2 already merged the LMS rebuild into `main` at `cae5c48`. The user clarified on 2026-10-05 that remaining fixes should be committed directly on current `main`, without another PR. Recovery commit `26bd011` is now a direct follow-up on local main; [PR #3](https://github.com/ghostiee-11/igot-skill-platform/pull/3) is superseded by that direct delivery. Preserve this preference for this recovery follow-up; do not open another PR for it.

Repository delivery: the user explicitly authorized documentation cleanup, committing the repairs on `rebuild/lms`, a PR targeting `main`, then its merge on 2026-10-04. Documentation and local verification are complete. Repair commit `d851676` was pushed and [PR #2](https://github.com/ghostiee-11/igot-skill-platform/pull/2) was created with the verified changes. That PR's GitHub state/checks/merge commit are the authoritative delivery record, so this handoff does not freeze a transient pre-merge status. Implementation source is `rebuild/lms`; default/target branch is `main`. Pre-LMS `main` baseline: `0d0f6d2`; use a merge commit to retain it and the LMS commit history.

Frontend: http://localhost:3000. The in-app browser is signed into the standard learner, enrolled in the CPI course, with a verified concept answer. All three login-screen demo personas authenticate. Detailed executed evidence and remaining limits: [local runtime receipt](local-runtime-2026-10-04.md). The earlier [read-only audit](local-validation-2026-10-04.md) describes the state before repair.

Latest follow-up: fixed the dashboard My Learning hover contrast in `apps/frontend/src/app/globals.css`. An obsolete light-hero rule used an opaque near-white hover fill while the final hero styling kept white text. Shared glass-action hover/focus now uses `--color-hero-action-hover` (white at 16% opacity over the dark hero). Docker frontend rebuilt successfully, all 30 static pages/TypeScript passed, and the new image is running healthy. Browser verified actual hover and keyboard-focus computed styles and readable label/icon; backend services remained running. No new unit tests were needed for this CSS-only change.

## Constraints and decisions

- Use existing `docs/` for continuity; preserve local configuration/data and volumes.
- Never store credentials or provider keys in handoff documents.
- Active runtime is service-based Compose; historical backend/content pipeline remain content and migration references.
- No legacy database existed in this checkout. Added an explicit local catalogue bootstrap from branch-authored source, not a historical learner-data import.
- Seed inserts missing catalogue records and refuses conflicting IDs. Existing account credentials/onboarding are preserved; learning read-model snapshots can refresh.
- User chose to keep existing apps open despite memory pressure. Do not close their apps.
- No factory reset, Windows reboot or volume deletion occurred. Repository commit/push/PR merge are now explicitly authorized as a separate delivery step.

## Implemented

- `infra/compose/docker-compose.yml`: restartable Debian-based PostgreSQL/RabbitMQ infrastructure, one-shot catalogue/demo bootstrap, assessment-event dispatcher, content worker.
- `infra/seed/` and `scripts/export-local-fixtures.py`: four courses, 12 modules, 27 lessons, three exams/21 questions, six technical labs, six cyber challenges, nine statistical items, four domains/35 competencies.
- `apps/frontend/Dockerfile`, `next.config.ts`: bounded webpack build, two page workers, standalone non-root runtime with public/static assets.
- `apps/gateway/src/igot_gateway/main.py`: profile aggregates identity/certificates/skills; dashboard uses actual identity/preferences.
- `services/assessment/.../dispatch_events.py`: retryable outbox delivery through existing idempotent service HTTP APIs.
- `services/learning/.../models.py` and migration `0002_certificate_attempt_ids`: UUID-compatible certificate attempt references.
- `services/content/.../tasks.py`: exclusive Celery control/event queues compatible with RabbitMQ 4.
- `scripts/start-local.ps1`: sequential build and health-gated startup, preserving volumes.
- `scripts/smoke-local.py`: live integration verification using separate test learners.

## Actually executed and tested

- Repaired Docker Desktop's inaccessible inference/secrets sockets by preserving their parent runtime directories; verified engine recovered with existing images retained.
- Diagnosed Windows Resource-Exhaustion-Detector events at Docker VM failures. Original WSL config backed up as `C:/Users/prath/.wslconfig.igot-backup-20261004`; applied `memory=2GB`, existing `swap=8GB` after full WSL shutdown. Other distributions were stopped. This host has a fixed 4 GB Windows pagefile.
- Rebuilt missing/damaged images. Content image's previous uvicorn/alembic scripts were zero bytes; fresh build fixed it.
- Frontend clean Docker production build passed compilation, TypeScript and all 30 static pages; runtime image about 439 MB.
- Full pre-PR rerun passed all 75 Python tests: gateway 36, identity 2, learning 2, assessment 15, competency 2, AI 3, content 5, labs 4 and legacy migration 6. Contract validation passed four event schemas/eight API exports. Checked 100 local links across 14 documentation entry points.
- Live smoke passed twice: demo login, registration/onboarding, four-course enrolment/player, lesson completion, grading, durable certificate, profile certificate aggregation, personalized dashboard, competency analysis/recommendations, adaptive grading, isolated technical grading, cyber notebook ingress/cleanup, generated quiz and interview turn/report.
- Browser verified login, catalogue, CPI syllabus, enrolment/player and correct concept grading.
- All three demo login personas authenticated with expected role/onboarding states.
- RabbitMQ content job completed at 100% after worker repair; pending assessment outbox count was zero.
- Repeated bootstrap inserted zero duplicate catalogue rows. Tests left separate test learners and test activity; no fabricated completion for the normal demo learner. Demo learner has CPI enrolment and one answered concept.
- Final fixture review corrected course skill links to the nine authored outcomes rather than linking every domain competency. The 35 links introduced by the first bootstrap were backed up and replaced; learner records were preserved. Taxonomy remains at 35 competencies.
- Compose configuration, startup-helper syntax and staged whitespace checks passed. Both `start-local.ps1 -SkipBuild` and the full default sequential build/start path were actually executed successfully. The documented `uv run --project services/assessment --frozen python scripts/smoke-local.py` passed after that restart.
- No labelled lab containers or networks remained after smoke cleanup.
- Latest service-status recheck: all eleven health-checked containers healthy, both workers running, frontend/gateway/domain HTTP probes returned 200, and one-shot jobs exited 0. AI readiness explicitly reports `degraded` with no configured live providers; deterministic fallback remains available. Health does not imply every feature is configured.

## Commands and locations

See [local setup](../LOCAL_SETUP.md), [architecture](architecture/service-architecture.md), [service catalogue](services/README.md), [bootstrap provenance](../infra/seed/README.md).

- Restart existing images: `powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -SkipBuild`.
- Build sequentially and start: `powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1` (stops services while building).
- Status/logs: `docker compose --env-file .env -f infra/compose/docker-compose.yml ps -a` / `logs --tail 100 <service>`.
- Live smoke: `services/assessment/.venv/Scripts/python.exe scripts/smoke-local.py`; creates separate local test activity.
- Service tests: `uv run --frozen --no-sync python -m pytest -q` inside each service/gateway/migration directory.
- Host Node 22.23.3, managed Python 3.12 via uv; system `python` is still 3.11.
- Original Docker image build log is in host temp as `igot-lms-compose-setup.log`.
- Runtime socket directories were preserved under `Docker/run.stale-igot-20261004*` and `docker-secrets-engine.stale-igot-20261004*` in local AppData.

## Remaining issues / next work

Post-merge host follow-up: PR #2 merged with all 24 checks successful and preserved `0d0f6d2`/LMS ancestry. Recovery commit `26bd011` adds guarded `-RepairDockerDesktop` startup mode. PowerShell 5.1 syntax checks and the actual recovery/start command passed; all 11 recovery-PR checks passed. It preserves stopped runtime directories, probes the engine and never changes WSL settings or removes data. The user chose direct main delivery instead of merging PR #3. This remains a recurring host workaround, not a permanent Windows/Desktop bug fix. Docker was unavailable at the latest 2026-10-05 status check; no restart was performed during the direct-commit request.

Local startup and core usability repair are complete. Repository delivery is tracked in [PR #2](https://github.com/ghostiee-11/igot-skill-platform/pull/2); check its current GitHub state and the checkout branch before continuing rather than relying on historical branch labels. Keep the stack running for the user. No additional implementation work is required for the validated local-runtime scope; remaining work is listed below.

- Frontend lint still has 81 errors / 102 warnings; production build passes.
- Provider speech/live-model calls and password recovery require configuration; fallback interview/quiz behavior was verified.
- Authored video quality needs review: CPI lesson 1's retained YouTube URL loads a price-action trading video. It was not silently replaced.
- Full production cutover, field-level legacy reconciliation, broker event publishing/consumption, lab expiry scheduling/isolation hardening and unlimited adaptive generation remain separate work. The new assessment dispatcher uses durable outbox + HTTP, not RabbitMQ delivery.
- See [known issues](known-issues.md) and [migration status](migration/status.md). Do not treat local runtime verification as production approval.
