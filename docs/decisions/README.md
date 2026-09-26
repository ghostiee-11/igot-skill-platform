# Architecture decisions

| Decision | Status | Effect |
|---|---|---|
| [0003: Domain services](0003-domain-services.md) | Accepted | Replaces the monolith deployment assumption; introduces owned services and schemas |
| [0004: Lab runtime](0004-lab-runtime.md) | Accepted | Separates control/execution; local containers first, cloud VM adapter later |

The [original monolith ADR](../adr/0001-modular-monolith-and-ai-boundary.md) and [LMS ownership ADR](../adr/0002-backend-owns-lms-data.md) are historical records. The prohibition on an AI-owned duplicate LMS datastore remains in effect.

New decisions use Context, Decision, Alternatives Considered, Consequences and Status. Record an intentional revision instead of silently rewriting history. Implementation status belongs in migration documentation, not a decision's acceptance status.
