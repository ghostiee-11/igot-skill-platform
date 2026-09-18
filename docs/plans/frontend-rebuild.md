# Deferred: fresh frontend

Status: planned; not part of service extraction.

The user explicitly requested moving the existing frontend as-is before separately redesigning it. `apps/frontend` therefore retains the present routes, components, styles, media hooks, language dictionaries and dependency lockfile. Only configuration and API compatibility changes necessary for relocation are in scope now.

Do not interpret preservation as endorsement of existing UX, state management or lint debt. Record defects without redesigning screens during backend migration.

A later specification must choose navigation, information architecture, screen journeys, visual direction, shared design system, API-client adoption, caching/state ownership, error recovery and accessibility criteria. The generated API contract is available as an input to that work. English/Hindi coverage and learner/admin roles remain product requirements unless explicitly revised.

Acceptance for this phase: route source and assets remain intact, the app starts from its new directory, configuration targets the gateway, and migrated journeys are verified without silently changing feature semantics.
