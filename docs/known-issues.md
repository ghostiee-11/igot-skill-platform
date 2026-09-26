# Known issues and limits

Last updated: 2026-09-25. See [migration status](migration/status.md) and the [runtime parity audit](migration/runtime-parity-audit-2026-09-23.md) for verification and repair follow-up.

## Inherited application debt

- Copied frontend lint debt: an earlier check reported 73 errors / 100 warnings. Relocation does not fix these.
- Original backend tests had six failures: two Marimo launch failures, three behavioural interview expectations/telemetry/scoring failures, and a Windows UTF-8 seed decoding failure. New services need independent verification.
- The [learner audit](lms-learner-audit.md) leaves server-side timing, retake policy, completion gating, generated-content review, login return handling and accessibility open.
- Draft designation targets and heuristic competency scores are not a validated civil-service measurement framework.

## Migration risks

- Splitting ownership can omit profile/certificate, course/assessment and dashboard fields expected by the copied frontend.
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
