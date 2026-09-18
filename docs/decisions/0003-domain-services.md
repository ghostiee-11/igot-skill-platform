# ADR 0003: Independently deployed domain services

Status: accepted, 2026-09-17.

## Context

The existing modular monolith mixes transport, domain rules, generation, runtime execution and persistence. The user requested independent services, inspired by `pj-030-ocg`, while retaining a prominent frontend application. This is an explicit revision of the earlier monolith deployment decision.

## Decision

Use identity, learning, assessment, competency, AI, content and labs services with a thin public gateway. Keep one shared assessment service with a registry of specialist engines so new learning domains can be added without adding a deployment. Each stateful service owns a PostgreSQL schema and role; stateless services do not get databases by default.

Preserve logical LMS data ownership, but distribute it by explicit domain ownership rather than a shared backend ORM. Services communicate by versioned APIs and durable events. Do not copy the reference project's process-and-file protocol into ordinary interactive request handling.

Move the frontend intact. Rebuilding its architecture and visual design is deferred until it can be specified and reviewed separately.

## Alternatives considered

- One modular backend: simpler operations, but does not meet the requested deployment independence.
- One service per competency domain: makes adding domains unnecessarily expensive and duplicates assessment lifecycle logic.
- A database for every service: unnecessary for stateless AI and gateway; schema isolation is sufficient for the first deployment when enforced with separate roles.

## Consequences

Cross-domain reads require APIs or owned projections. Completion/evidence flows need idempotent delivery and eventual-consistency handling. More services require explicit local orchestration, contracts and observability. Import-time seeding and a shared ORM model are incompatible with the new architecture.

The original ADRs remain historical records. This ADR supersedes their single-backend deployment assumption, not their prohibition on a duplicate AI-owned LMS store.
