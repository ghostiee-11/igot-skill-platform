# Public API compatibility inventory

Baseline: `7123bd3`. The old application declares 92 router operations and mounts several repeatedly. The new gateway must map each supported operation once. `/api/v1` compatibility aliases may normalize to `/api`; aliases must not create duplicate application router registrations.

This is the route-family checklist for migration verification, not a claim every operation has been ported. See [status](status.md).

| Existing `/api` family | Owner / aggregation | Operations to preserve |
|---|---|---|
| `/auth` | Identity | Login, register, me, password-recovery response |
| `/onboarding` | Identity | Status, save |
| `/profile/` | Identity + learning + competency | Read profile/certificates/skills, update profile |
| `/discover/courses` | Learning | Search, filters, pagination, recent searches |
| `/courses/{id}` | Learning + assessment metadata | Detail and enrollment |
| `/learning/course/{id}/player` | Learning | Syllabus, selected lesson and progress |
| `/learning/lesson/{id}` | Learning | Complete and activity submission |
| `/dashboard/summary` | Learning with owned-domain read models | Personalized dashboard |
| `/assessments/{id}` | Assessment; completion to learning | Test delivery and submission |
| `/admin/overview`, `/admin/assign-course`, `/admin/courses` | Learning with identity/assessment aggregation | Workforce overview, assignment, course creation |
| `/admin/competency-analytics`, `/admin/courses/{id}/reindex` | Competency | Analytics and index update |
| `/competency` | Competency | Domain detail, analyze, profile, gaps |
| `/recommendations` | Competency + learning enrollment | Generate, list, status update |
| `/quiz` | Assessment + content extraction + AI | Generate, list, get, submit, attempts, delete |
| `/stats-engine/health`, `/stats/calculate`, `/charts/generate` | Assessment statistical engine | Health, calculations and chart specifications |
| `/questions` | Assessment statistical engine | Generate, adaptive next and submit |
| `/competencies`, `/users/{id}/competencies` | Assessment statistical engine | Engine vocabulary and learner mastery; enforce learner/admin ownership |
| `/behavioural/courses`, `/behavioural/corpus`, `/behavioural/cases` | Assessment + learning/content | Course case metadata, corpus, cases and generation |
| `/behavioural/session` | Assessment | Start, current, submit, summary |
| `/behavioural/interview` | Assessment + AI speech/generation | Transcribe, start, turn, end (both historical end forms) |
| `/technical-courses/process`, `/objectives`, `/decide-mode`, `/templates`, `/match-template` | Content intake + assessment | Transcript, objectives, mode and template selection |
| `/technical-courses/labs`, `/pipeline/run-full` | Assessment + AI + labs | List/detail, generation, solution, validation and pipeline orchestration |
| `/technical-courses/labs/{id}/assistant`, `/execute` | Assessment + AI/labs | Guided assistance and grading execution |
| `/technical-courses/sandbox/execute-code`, `/notebook/export` | Labs | Cell execution and export |
| `/digital-governance/scenarios` | Assessment | Catalogue, detail, start, answer and summary |
| `/digital-governance/sandbox` | Assessment definitions + labs control | Challenges, knowledge base, generation, start/get/stop, flags, hints and competency radar |
| `/agents/chat` | AI with authorized domain adapters | Tutor, gaps, recommendations and quiz navigation |

## Compatibility rules

Keep methods, query parameters, multipart bodies, JSON field names and status semantics needed by the copied frontend. Route-name similarity alone is not compatibility. Private routes must still enforce authorization when called directly on a service.

Required checks include optional trailing slashes, multipart uploads, upstream failure translation, request timeouts and binary responses. Browser lab access additionally requires WebSocket/stream proxy checks rather than ordinary JSON-only tests.

Unknown routes return an explicit error. Known but unmigrated operations must be reported as such; they must not silently fall back to the old monolith or return fabricated success.
