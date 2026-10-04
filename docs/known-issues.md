# Known issues and limits

Last updated: 2026-10-04. See [local runtime verification](local-runtime-2026-10-04.md), [migration status](migration/status.md) and the [runtime parity audit](migration/runtime-parity-audit-2026-09-23.md).

## Inherited application debt

- Copied frontend lint debt: current check reports 81 errors / 102 warnings; clean container production build passes.
- Retained authored media needs review: the CPI lesson 1 YouTube URL loads a price-action trading course instead of official CPI instruction. Local bootstrap preserves branch content rather than silently substituting media.
- Password-recovery delivery and semantic vector indexing remain unconfigured. Live speech/model features require provider keys; deterministic interview/quiz fallbacks work locally.
- Original backend tests had six failures: two Marimo launch failures, three behavioural interview expectations/telemetry/scoring failures, and a Windows UTF-8 seed decoding failure. New services need independent verification.
- The [learner audit](lms-learner-audit.md) leaves server-side timing, retake policy, completion gating, generated-content review, login return handling and accessibility open.
- Draft designation targets and heuristic competency scores are not a validated civil-service measurement framework.

## Migration risks

- Profile certificate/skill aggregation and dashboard identity personalization were repaired and verified on 2026-10-04; full compatibility inventory still needs separate cutover review.
- Assessment completion now has a retryable outbox-backed HTTP dispatcher, verified with real PostgreSQL certificates and duplicate handling. RabbitMQ event publication/consumption and broader recovery tests remain separate work.
- Evidence/completion delivery must survive retries and restarts; a synchronous happy path is insufficient proof.
- PostgreSQL role isolation cannot be established with SQLite unit tests.
- Migration must preserve IDs, hashes, historical payloads and optional content-pipeline resources; count-only checks are insufficient.
- Root `.env` may target hosted resources. New checks require explicit isolated configuration.
- Local containers are not cloud VMs. Privileged penetration-testing exercises remain deferred.
- The disposable PostgreSQL apply and count reconciliation pass, but field-level hashes/timestamps and rollback restoration are not yet verified.
- The repaired behavioural generator creates a generic branching case grounded in supplied notice text; it is not a verified statutory interpretation or LLM-authored case. Adaptive statistical practice currently draws from a finite imported question bank rather than generating unlimited variants.
- The local labs controller mounts the Docker socket and is therefore a development boundary, not an acceptable shared production placement.
- Cyber incident Marimo workspaces are reachable through a short-lived bearer URL on local port 8107. This preserves the workspace's internal Docker network for local testing, but the labs controller and its Docker-socket mount must be replaced or hardened before shared deployment.

## Deferred

[Fresh frontend](plans/frontend-rebuild.md), [cloud VM runtime](plans/cloud-vm-labs.md), production data cutover and rebuild merge pending user review.
