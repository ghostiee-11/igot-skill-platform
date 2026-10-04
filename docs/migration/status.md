# Service migration status

Last updated: 2026-10-04. LMS source branch: `rebuild/lms`; default/target: `main` through [PR #2](https://github.com/ghostiee-11/igot-skill-platform/pull/2), whose live GitHub state records the integration result. Production data cutover is separate.

## Current local evidence (2026-10-04)

The [executed local runtime receipt](../local-runtime-2026-10-04.md) is the current operational evidence. Eleven health-checked containers are healthy, both workers run, explicit local seed jobs exit successfully, and authenticated core gateway journeys were executed. Frontend clean production build/TypeScript passed; inherited lint remains a non-blocking CI baseline. The full pre-PR rerun passed 75 Python tests plus contract validation. The documented default sequential build/start path and subsequent smoke command were actually executed successfully.

Local startup now includes the authored four-course bootstrap and separate demo personas, retryable assessment outbox delivery through idempotent HTTP APIs, UUID-compatible certificate references, profile/dashboard aggregation, and a RabbitMQ content worker. Actual live checks include certificates, technical Docker grading, cyber HTTP ingress, quiz generation, interview fallback and a completed extraction job. This proves local core usability, not every specialist route, production recovery, WebSocket coverage or model/provider integration.

The checked pre-LMS `main` baseline is `0d0f6d2`, already a service-architecture merge. The six LMS branch commits inherited its Dockerfiles/Compose unchanged; the current PR adds explicit local runtime repairs and accurate documentation. The user authorized the repository merge on 2026-10-04. No legacy learner data was imported on this host; no source SQLite database was present. Historical import rehearsals below belong to earlier dated sessions.

## Historical implementation record (through 2026-09-25)

The 2026-09-23 baseline below is historical. The [runtime parity audit](runtime-parity-audit-2026-09-23.md#repair-follow-up-2026-09-25) tracks the later local curriculum import and repaired scenario, lab, quiz, adaptive and behavioural-case contracts. These changes now pass service tests and have been deployed through the local Compose stack.

Local follow-up: Docker was started and the current stack rebuilt. The statistical exam's empty-chart payload crash is fixed and verified in both question modes in the browser. The Digital Governance incident launcher now obtains the authored challenge from assessment, starts its isolated Marimo notebook through labs, and serves it via a token-scoped HTTP/WebSocket proxy; Incident Module 1 and its notebook content were verified in the browser. This remains a local-development runtime, not production sandbox authorization.

## Historical baseline

- `main` fast-forwarded from `5a72a4c` to `7123bd3`, incorporating `final-final`, and was pushed to `origin/main`.
- Rebuild branch was created from that baseline; at that historical point it was awaiting user approval for merge. Current merge authorization is recorded above.
- Existing user modification to `.gitignore` (ignoring `restructure/`) was preserved.
- Historical baseline check: Python 3.11 with isolated SQLite reported 149 passed / 6 failed; TypeScript passed; ESLint reported 73 errors / 100 warnings. These are earlier baseline observations, not validation of this branch.

## Historical integration checks (through 2026-09-25)

- All Python applications have committed `uv.lock` files. Their Dockerfiles install with `uv sync --frozen` and all eight application images build successfully.
- Service and migration suites: **59 passed** (gateway 32, identity 2, learning 2, assessment 7, competency 2, AI 3, content 4, labs 2, legacy migration 5). Behavioural interview coverage includes mocked adaptive turns, reports, restart persistence and speech upload. A live gateway check also returned a Groq follow-up and a Groq-scored report. The only reported warnings are upstream Starlette/httpx deprecations.
- Frontend: `npx tsc --noEmit` passed. A clean Docker production build compiled all 30 routes, completed TypeScript checking and generated every static page. The host-only build remains susceptible to a Windows lock on `.next/trace`; `.next` is excluded from Docker context.
- `docker compose --env-file .env -f infra/compose/docker-compose.yml config --quiet` passed. PostgreSQL, RabbitMQ, identity, learning, assessment, competency, AI, content, labs and gateway were started locally; every health endpoint responded and labs readiness confirmed database plus Docker access.
- Alembic ran at container startup using schema-scoped service roles. Schemas are provisioned by the database bootstrap, while migrations create only owned tables and their schema-local version tables.
- PostgreSQL schema privilege matrix was checked for all six service roles against all six schemas (36 combinations): each role has USAGE/CREATE on its own schema only; all cross-service combinations are denied.
- The real `backend/karmayogi.db` was inventoried and applied to a fresh local PostgreSQL rehearsal database. Every populated table has a typed destination. All 35 source-to-destination count checks matched, a second apply was idempotent, insert failures are now reported separately from unique-key skips, and PostgreSQL sequences were advanced to imported maxima. This includes 6 cyber challenges, 5 cyber sessions, 6 cyber templates, 10 generated quiz questions, 1 generated quiz, 7 statistical questions and 6 technical lab templates. Remaining archive categories currently contain zero rows.
- An authenticated local lab lifecycle created an internal network, allowlisted target and Marimo workspace, reached `running`, terminated, and left zero labelled containers and zero labelled networks.
- Frontend preservation was checked against all 145 baseline tracked files: only its `.gitignore` differed after relocation.

## Remaining production/cutover work

The [2026-09-23 runtime parity audit](runtime-parity-audit-2026-09-23.md) records the original failures and subsequent repair follow-up.

- Complete remaining generated-case/browser scenario branching and WebSocket journeys. The current restarted local stack's adaptive grading, quiz generation, technical grading and cyber HTTP ingress were verified on 2026-10-04.
- Decide whether notice-based cases require model-authored branching and expert statutory review; the current generic decision tree preserves source text and durable session behavior but is not a legal interpretation.
- Extend reconciliation beyond counts: verify ID sets, password hashes, JSON payloads and timestamps, then rehearse rollback/restore from a database snapshot.
- Extend the executed gateway smoke and browser login/player/concept checks to full browser exam/certificate-modal and WebSocket interactions.
- Add broker event publishers/consumers and broader recovery tests. The current assessment HTTP dispatcher delivers committed outbox events, but does not replace the planned broker transport.
- Resolve inherited frontend lint debt and the host `.next/trace` lock separately from the clean container build.

The table below is the historical migration assessment from 2026-09-25. Current local verification is recorded at the top of this document; production completeness is still separate.

| Area | Historical state | Evidence required before marking production/cutover complete |
|---|---|---|
| Frontend relocation | Structurally verified | Compatible end-to-end API journeys and lint remediation |
| Gateway and local infrastructure | Baseline verified | Full compatibility-route parity and production health policy |
| Identity, learning, competency | Baseline verified | Full browser learner journey and event recovery |
| Assessment, AI, content | In progress | Engine parity, durable results/jobs, evidence provenance and provider behavior |
| Local lab runtime | Baseline verified | Ingress/WebSocket test, scheduled reconciliation and adversarial isolation review |
| Data migration | Disposable apply verified | Field/hash reconciliation and rollback rehearsal |
| Documentation | In progress | Source links and commands reconciled against actual implementation |
| Fresh frontend | Deferred | Separate product/design specification |
| Cloud VM labs | Deferred | Separate provider, lifecycle and deployment plan |

Do not remove the original backend, content pipeline or migrations until their replacement is verified against the ownership inventory. Do not run migration against a live database during development. A successful unit test suite does not prove PostgreSQL role isolation, broker recovery or browser interoperability.
