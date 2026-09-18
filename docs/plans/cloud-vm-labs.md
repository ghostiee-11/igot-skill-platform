# Deferred: cloud VM lab runtime

Status: planned after the rest of the application rebuild and local lab integration.

The intended environment is a separate cloud VM execution boundary supporting penetration-testing exercises. This phase does not select a provider, spend a cloud budget, provision machines or expose a public target.

The local runtime adapter establishes a common lifecycle: provision, status, access, execute, reset, terminate and collect artifacts. Cloud implementation must preserve that application contract while defining VM-specific isolation, networking and recovery.

Decisions required before cloud implementation:

- Provider, region, image registry, cost limits, concurrent-session quotas and idle shutdown.
- VM per learner/session versus approved pooled images, and the isolation implications.
- Browser terminal/desktop access, authentication, private connectivity and certificate management.
- Authorized target networks and egress controls; no unrestricted access to third-party targets.
- Image hardening, patching, snapshot/reset policy, artifact retention and deletion.
- Provisioning failure recovery, orphan reconciliation, incident response and operational ownership.

The VM phase requires its own infrastructure plan and deployment approval. Local containers are useful for development and bounded exercises but do not prove cloud isolation or privileged exercise support.
