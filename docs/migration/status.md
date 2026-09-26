# Service migration status

Last updated: 2026-09-25. Branch: `rebuild/service-architecture`.

The 2026-09-23 baseline below is historical. The [runtime parity audit](runtime-parity-audit-2026-09-23.md#repair-follow-up-2026-09-25) tracks the later local curriculum import and repaired scenario, lab, quiz, adaptive and behavioural-case contracts. These changes now pass service tests and have been deployed through the local Compose stack.

Local follow-up: Docker was started and the current stack rebuilt. The statistical exam's empty-chart payload crash is fixed and verified in both question modes in the browser. The Digital Governance incident launcher now obtains the authored challenge from assessment, starts its isolated Marimo notebook through labs, and serves it via a token-scoped HTTP/WebSocket proxy; Incident Module 1 and its notebook content were verified in the browser. This remains a local-development runtime, not production sandbox authorization.

## Verified baseline

- `main` fast-forwarded from `5a72a4c` to `7123bd3`, incorporating `final-final`, and was pushed to `origin/main`.
- Rebuild branch created from that baseline. It is not approved for merge into main.
- Existing user modification to `.gitignore` (ignoring `restructure/`) was preserved.
- Historical baseline check: Python 3.11 with isolated SQLite reported 149 passed / 6 failed; TypeScript passed; ESLint reported 73 errors / 100 warnings. These are earlier baseline observations, not validation of this branch.

## Integration checks performed during implementation

- All Python applications have committed `uv.lock` files. Their Dockerfiles install with `uv sync --frozen` and all eight application images build successfully.
- Service and migration suites: **59 passed** (gateway 32, identity 2, learning 2, assessment 7, competency 2, AI 3, content 4, labs 2, legacy migration 5). Behavioural interview coverage includes mocked adaptive turns, reports, restart persistence and speech upload. A live gateway check also returned a Groq follow-up and a Groq-scored report. The only reported warnings are upstream Starlette/httpx deprecations.
- Frontend: `npx tsc --noEmit` passed. A clean Docker production build compiled all 30 routes, completed TypeScript checking and generated every static page. The host-only build remains susceptible to a Windows lock on `.next/trace`; `.next` is excluded from Docker context.
- `docker compose --env-file .env -f infra/compose/docker-compose.yml config --quiet` passed. PostgreSQL, RabbitMQ, identity, learning, assessment, competency, AI, content, labs and gateway were started locally; every health endpoint responded and labs readiness confirmed database plus Docker access.
- Alembic ran at container startup using schema-scoped service roles. Schemas are provisioned by the database bootstrap, while migrations create only owned tables and their schema-local version tables.
- PostgreSQL schema privilege matrix was checked for all six service roles against all six schemas (36 combinations): each role has USAGE/CREATE on its own schema only; all cross-service combinations are denied.
- The real `backend/karmayogi.db` was inventoried and applied to a fresh local PostgreSQL rehearsal database. Every populated table has a typed destination. All 35 source-to-destination count checks matched, a second apply was idempotent, insert failures are now reported separately from unique-key skips, and PostgreSQL sequences were advanced to imported maxima. This includes 6 cyber challenges, 5 cyber sessions, 6 cyber templates, 10 generated quiz questions, 1 generated quiz, 7 statistical questions and 6 technical lab templates. Remaining archive categories currently contain zero rows.
- An authenticated local lab lifecycle created an internal network, allowlisted target and Marimo workspace, reached `running`, terminated, and left zero labelled containers and zero labelled networks.
- Frontend preservation was checked against all 145 baseline tracked files: only its `.gitignore` differed after relocation.

## Remaining work before cutover

The [2026-09-23 runtime parity audit](runtime-parity-audit-2026-09-23.md) records the original failures and subsequent repair follow-up.

- Validate the newest adaptive statistical and generated-case changes through a restarted Compose stack. The earlier lesson import, scenarios, technical lab and quiz generation were verified live locally.
- Decide whether notice-based cases require model-authored branching and expert statutory review; the current generic decision tree preserves source text and durable session behavior but is not a legal interpretation.
- Extend reconciliation beyond counts: verify ID sets, password hashes, JSON payloads and timestamps, then rehearse rollback/restore from a database snapshot.
- Exercise the complete browser learner journey through the gateway, including registration, enrolment, course completion, assessment evidence, quiz generation and lab ingress/WebSocket proxying.
- Add durable outbox publishers/consumers and recovery tests; persisting outbox records alone does not deliver events.
- Resolve inherited frontend lint debt and the host `.next/trace` lock separately from the clean container build.

| Area | State | Evidence required before marking complete |
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
