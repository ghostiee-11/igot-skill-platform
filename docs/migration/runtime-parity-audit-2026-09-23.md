# Runtime parity audit — 2026-09-23

Scope: the current Compose stack, the copied frontend's API calls, gateway mappings, service implementations, and the legacy SQLite database. This is a read-only audit of application data and endpoints; no production or local data import was performed.

## What was verified

- All Compose services were healthy when checked.
- The standard learner account authenticated through the public gateway.
- Public `GET` routes for authentication, profile, dashboard, discovery, course detail, quizzes, recommendations, behavioural courses/cases, technical templates, cyber challenges, and statistical-engine health returned `200`.
- `/competency/gaps` returned `404` because this learner has not run gap analysis. This is an expected empty state: the frontend recognizes the "No gap analysis" detail and offers the analysis action.

## Confirmed discrepancies

| Priority | Learner journey | Evidence | Cause and repair boundary |
|---|---|---|---|
| P0 | Open a course lesson | `GET /api/learning/course/1/player` returned `404`. Legacy SQLite has **11 modules and 14 lessons** across its four courses; active PostgreSQL `learning` has **0 modules and 0 lessons**. | Reconcile and import curriculum into the learning schema, preserving IDs, ordering, lesson content, and progress. Do not treat a course catalogue row as a complete course. |
| P0 | Take a course exam | `GET /api/assessments/1` returned `404`. Legacy SQLite has **3 assessments and 21 questions**; active PostgreSQL `assessment` has **0 assessments and 0 questions**. | Reconcile and import assessment definitions/questions, verify answer-key confidentiality, then test submission and certificate/completion effects end to end. |
| P0 | Open digital-governance tabletop scenarios | `GET /api/digital-governance/scenarios` returned `404`. The gateway advertises the scenario family, but assessment has no matching route. The legacy backend contains the scenario catalogue and branching session engine. The frontend previously swallowed the load error and displayed an empty directory; it now shows the actual failure. | Port catalogue and session operations to assessment-owned durable storage, including restart recovery and the frontend's response fields. |
| P0 | Open hands-on labs | `GET /api/technical-courses/labs` returned `404`. The gateway advertises catalogue/detail/assistant/execute routes, but assessment does not implement the catalogue or detail, and labs does not implement the legacy execution contract. Six templates exist in the active assessment database, but templates are not runnable generated labs. | Migrate lab definitions and implement assessment/labs contracts before presenting this as a working learner activity. |
| P1 | Generate a quiz from an upload | The frontend calls `POST /api/quiz/generate`; the gateway maps it to assessment, but assessment has no route. Existing imported quizzes can be listed and taken. | Restore the upload/extraction/generation pipeline with authenticated ownership and generated-question validation. |
| P1 | Use the adaptive statistical exam | The frontend calls `POST /api/questions/next` and `/submit`; gateway mappings exist, but assessment implements neither route. | Port question selection, answer checking, mastery state, and ownership checks. The current `/stats/calculate` and `/charts/generate` routes do not replace this flow. |
| P1 | Generate and resume a behavioural case | Course-linked generation currently ignores the frontend's `custom_notice_text` and clones the same Rule 14 template. Generated cases are appended to the module-level `CASES` list; only their ID is stored in a session. A service restart removes the generated case, making active sessions unresolvable. | Store generated case definitions in assessment-owned durable storage, derive them from the submitted notice, and bind sessions to a stable case version. |
| P1 | Ground the behavioural interview in full course material | The new protected learning endpoint can supply modules and lessons, but current course 1 has no module or lesson records. A verified Groq interview therefore used its 221-character course overview. Legacy course 1 has **3 modules and 2 lessons**. | Import/reconcile lesson data, then verify the interview context contains the original content. The Groq integration itself was verified live. |

## Next execution order

1. Prepare a field-level comparison and recoverable backup for the active local database; rehearse importing learning modules/lessons and assessment questions from `backend/karmayogi.db`. The existing `migrations/legacy/migrate.py` was designed for a disposable target and is not an approved blind import into an active database.
2. Restore the scenario and technical-lab API contracts with durable sessions and frontend-shaped responses.
3. Restore quiz generation and adaptive statistical question workflows.
4. Add gateway-through-browser smoke checks for each repaired learner journey. A route resolving in the gateway is not proof that the destination exists or that its response matches the frontend.

This audit does not claim that every frontend workflow was exercised; it identifies the highest-impact discrepancies found in the first API and data parity sweep.
