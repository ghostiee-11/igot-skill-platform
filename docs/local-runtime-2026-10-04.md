# Executed local runtime verification

Date: 2026-10-04 (Asia/Calcutta). Branch: `rebuild/lms`. Owner: primary agent, no delegation.

## Outcome

The service-based platform is running on the user's Windows host. Frontend is at http://localhost:3000, gateway at http://localhost:8000. All eleven health-checked components are healthy; assessment-event and content workers are running. Catalogue/lab-image bootstrap containers exit with code zero as intended. Existing volumes/configuration were preserved.

## Docker repair actually executed

- Started Docker Desktop and confirmed that only six domain images and two lab runtime images existed; no platform stack had been created.
- Built the missing labs controller, gateway and frontend images.
- Diagnosed the reported Desktop startup errors against inaccessible `dockerInference` and then `docker-secrets-engine/engine.sock` objects. Individual socket renaming also failed. Preserved/recreated their parent temporary runtime directories after stopping Desktop. This is the directory workaround recorded in [Docker's matching issue report](https://github.com/docker/desktop-feedback/issues/554); the host repair did not touch Docker's WSL data directory.
- Correlated interrupted downloads/builds and Docker VM restarts with Windows low-virtual-memory events. The host has 16 GB physical RAM and a fixed 4 GB Windows pagefile. Backed up the original WSL config, applied a 2 GB WSL memory cap with its existing 8 GB swap, and shut down WSL to apply it. Other distributions were stopped. User explicitly chose to keep existing apps open.
- Downloaded runnable PostgreSQL 16 Bookworm and RabbitMQ 4 management images after a missing-blob failure in the interrupted Alpine image download. PostgreSQL's binary returned its version successfully before startup.
- Found zero-byte uvicorn/Alembic launcher files in the old content image. Rebuilt that image without cache; it migrated and started successfully.
- Built the frontend with bounded Node heap, webpack memory optimizations and two static-generation workers. Clean production compilation, TypeScript checking and all 30 static pages passed. Standalone runtime image is approximately 439 MB and runs as the Node user.

No factory reset, Windows reboot, volume erase, Git commit, merge or push was performed. WSL configuration was changed on this host; original backup location is in [handoff](HANDOFF.md).

## Implemented local startup behavior

- Explicit `local-seed` job after service migrations, before gateway startup. Versioned fixture contains branch-authored courses/curriculum/exams/labs/taxonomy. See [provenance](../infra/seed/README.md). Repeated startup inserts zero duplicate catalogue rows and preserves existing credentials/onboarding/history.
- Final review corrected course outcomes to the nine source-authored skills. The first export had over-linked the domain taxonomy; its 35 bootstrap-created links were backed up and replaced with the nine authored links. No learner progress, credentials or certificates were removed.
- Local demo personas match all three existing login-screen buttons. Admin authenticates as admin, standard learner is onboarded, and new officer retains an incomplete onboarding state.
- Gateway `/profile/` combines identity with learning certificates and competency skills. Dashboard uses current identity/profile values instead of placeholder names.
- Assessment outbox worker retries delivery through learning/competency idempotent HTTP APIs; completed exams now create persistent certificates/completion. Learning migration stores UUID attempt references as strings.
- Content Celery worker consumes RabbitMQ jobs. RabbitMQ 4 rejected its non-exclusive transient control queues initially; exclusive control/event queues fixed worker startup. The queued verification source was extracted successfully to an ignored artifact, with job status `completed`, progress 100 and no error.
- `scripts/start-local.ps1` performs sequential builds and waits for startup. Its syntax, `-SkipBuild` startup and full default sequential build/start path were actually verified. The default path was replayed after the documentation cleanup and restored the healthy running stack with data retained.

## Test and live execution evidence

Full pre-PR rerun: **75 tests passed** (gateway 36, identity 2, learning 2, assessment 15, competency 2, AI 3, content 5, labs 4, legacy migration 6). Warnings are upstream Starlette/httpx/anyio deprecations. Contract validation passed four event schemas/eight API exports; 100 local documentation links were checked across 14 entry documents.

`scripts/smoke-local.py` passed live against the gateway during initial repair and again after the documented full build/start command, using separate test learners:

- Login, registration, onboarding, four-course discovery/detail/enrolment/player, lesson completion.
- Course exam delivery with private answer keys, grading and real PostgreSQL certificate records; dashboard completion and profile certificate aggregation.
- Competency analysis across four domains and recommendation generation.
- Adaptive statistical MCQ delivery and correct-answer/mastery grading.
- Six technical lab definitions, real isolated Docker execution and passing template tests.
- Cyber incident workspace startup, Marimo HTTP ingress and session termination.
- Generated quiz delivery and behavioural interview start/turn/report; behavioural/scenario catalogues were also checked.

Browser verification: standard learner login, all four catalogue courses, CPI syllabus, enrolment/player, YouTube iframe loading and correct in-lesson concept feedback. The standard learner has a real CPI enrolment and one concept response; no exam certificate was fabricated for that account. Smoke learners retain their explicit test records.

Final data checks found four courses, 27 lessons, two smoke certificates and zero pending assessment outbox events. No labelled lab containers/networks remained after smoke cleanup. Actual provider speech/model calls, full scenario branching and complete browser exam/certificate-modal interactions were not claimed as tested.

## Remaining limits

See [known issues](known-issues.md) and [migration status](migration/status.md). Lint remains at 81 errors / 102 warnings. Password recovery and semantic indexing require configuration; provider keys are needed for live speech/model behavior. Retained CPI lesson 1 media loads a price-action trading course, so educational media still needs review. Outbox delivery is HTTP, not broker event delivery. Production migration/cutover, field-level reconciliation, scheduled lab expiry cleanup, shared-host isolation and expanded adaptive generation remain separate work.

## Reproduce

From repository root with Docker Desktop running:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -SkipBuild
services/assessment/.venv/Scripts/python.exe scripts/smoke-local.py
```

The smoke command creates local test activity. For rebuilding and setup details use [LOCAL_SETUP.md](../LOCAL_SETUP.md).
