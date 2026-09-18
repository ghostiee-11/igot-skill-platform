# Product capabilities during service migration

All backend capabilities below are in migration until the [verification record](../migration/status.md) says otherwise. These are retained user intents, not assertions of full parity.

| Capability | Owner | Existing UI | Required verification |
|---|---|---|---|
| Identity and onboarding | Identity | Login, register, onboarding, profile | Existing credentials/IDs work; active/role checks protect operations |
| Catalogue and enrollment | Learning | Courses, discover, course detail | Search, ordered syllabus, enroll/resume and assignments preserve references |
| Player and progress | Learning | Learn, my learning | Markdown/video/activity content, lesson navigation, durable progress |
| Exams and certification | Assessment + Learning | Assess, certificates | Server-owned grading, attempt history, stable learning-owned certificates |
| Dashboards/admin | Owning domain + gateway | Home, admin | User-specific summaries and role-checked operations |
| Competency intelligence | Competency | Competency overview/domain | Traceable evidence, explicit targets and historical gaps |
| Recommendations | Competency | Recommendations | Candidate courses from learning; acted-on statuses preserved |
| Generated quizzes | Assessment + Content + AI | Quiz hub/take | Extract, generate validated drafts, hide answers, persist attempts |
| Statistical engine | Assessment | Statistical exam | Numerical methods, tolerance, generation, mastery and branching |
| Behavioural cases/interviews | Assessment + AI | Cases, interview | Course-grounded sessions, persisted outcomes, explicit fallback provenance |
| Governance scenarios | Assessment | Governance scenarios | Branching and results; no answer leakage in active questions |
| Technical labs | Assessment + Labs | Lab workspace | Server-defined exercises/hidden tests, isolated execution and notebook export |
| Cyber labs | Assessment + Labs | Cyber sandbox | Definitions, ownership, browser access, hints/results and cleanup |
| Assistant | AI with domain adapters | Floating assistant | Backend-only keys; learner context/actions authorized |
| Content ingestion | Content | Upload/resource flows | Source provenance, extraction, durable processing and publication |
| Institutional/bilingual UI | Frontend | Public/authenticated routes | Copy unchanged; redesign deferred |

## Shared assessment engine contract

Each engine declares supported modes and provides definition validation, start/resume, submission, finalization and evidence production. Streaming and execution are optional capabilities. Adding a domain requires an engine, fixtures, grading tests, evidence mapping and a documented journey, not another deployment.

Assessment owns attempts, timestamps, learner association and grades. Engines never write another service's database. Active responses must exclude reference answers, optimal choices and hidden tests. Results identify their engine/version and whether evaluation is deterministic, generated or estimated.
