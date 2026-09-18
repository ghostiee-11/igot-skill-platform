# Known issues and limits

Last updated: 2026-09-18. See [migration status](migration/status.md) for current verification.

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
- Specialist compatibility remains incomplete for behavioural sessions, statistical mastery, generated technical labs and digital-governance session actions.
- The local labs controller mounts the Docker socket and is therefore a development boundary, not an acceptable shared production placement.

## Deferred

[Fresh frontend](plans/frontend-rebuild.md), [cloud VM runtime](plans/cloud-vm-labs.md), production data cutover and rebuild merge pending user review.
