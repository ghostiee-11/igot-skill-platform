# ADR 0004: Separate lab control from execution

Status: accepted, 2026-09-17.

## Context

The old backend launches Marimo processes and can fall back to executing learner Python in a host subprocess. The requested end state includes cloud VMs for penetration-testing labs, but that cloud implementation is intentionally deferred until the rest of the rebuild is finished.

## Decision

Use a labs service to own session lifecycle and a runtime adapter to provision, inspect, grant access, execute, reset, collect artifacts and terminate sessions. Implement the first adapter with disposable Docker workspaces and optional exercise target containers. Browser access is authenticated and session-scoped. No host-execution fallback is allowed.

Only the controller may reach the runtime control endpoint. Workspace and target containers receive no Docker socket, application credentials or access to application networks. Use explicit CPU, memory, process, duration and output limits. Default execution networks are isolated; provision dependencies in images rather than permitting unrestricted downloads during exercises.

## Alternatives considered

- Continue local Python/Marimo subprocesses: cannot establish the required isolation boundary.
- Provision real cloud VMs immediately: contradicts the requested implementation order and requires provider/budget decisions.
- Put labs inside assessment: couples learner code execution to grading and application credentials.

## Consequences

Container exercises cannot promise a full VM, kernel isolation or arbitrary privileged penetration testing. Such exercises remain cloud-phase work. Production execution hosts must be separated from the application host. Runtime state must be reconciled after controller restarts, not merely cleaned up by request handlers.
