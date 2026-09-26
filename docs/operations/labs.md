# Lab lifecycle and execution operations

## Boundary

The application stores session ownership, state, expiry and artifact references. Runtime workspaces contain only exercise data. Do not run the controller beside sensitive application workloads in a production deployment merely because local Compose allows it.

Local containers support browser notebooks/terminals and explicitly configured target exercises. They are not full cloud VMs. Cloud provisioning is deferred; see [the cloud runtime plan](../plans/cloud-vm-labs.md).

## Required lifecycle

1. Authenticate the learner and authorize the requested exercise.
2. Persist a provisioning request with a stable idempotency key.
3. Create the session network, workspace and optional target resources with session labels and expiry.
4. Issue short-lived, session-scoped browser access only after readiness succeeds.
5. Execute or submit using server-owned test configuration. Bound output and resource use.
6. Store results/artifact references and terminate or reset the runtime on request/expiry.
7. Reconcile persisted sessions against labelled runtime resources after restart and on a schedule.

Failure states must be visible to users; a container launch failure must never return a usable-looking workspace URL. Cleanup must handle partially created resources and repeated requests.

## Operator checks

- A different learner cannot inspect, enter, execute in, reset or terminate a session they do not own.
- Access tokens expire and cannot be replayed across sessions.
- Workspace and target networks cannot reach PostgreSQL, broker, identity or the Docker daemon.
- Container images run with least privilege, bounded resources, no host mounts and no privileged mode.
- Hidden tests and reference answers are not sent as browser-visible metadata.
- Expired/orphaned containers and networks are reclaimed, including after worker failures.
- Logs include session and correlation identifiers without tokens, secrets or full learner recordings.

## Local verification

The default local stack builds the controller and both allowlisted runtime images:

```powershell
docker compose --env-file .env -f infra/compose/docker-compose.yml up -d --build
```

`GET http://localhost:8107/v1/ready` checks both PostgreSQL and Docker access. The demo target exists to verify lifecycle and isolation plumbing; it is explicitly not an intentionally vulnerable target.

Exact implemented commands and verified coverage belong in [migration status](../migration/status.md); these requirements are not a certification of the local adapter.
