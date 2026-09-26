# Legacy data ownership and migration

Status: migration specification. Rehearsal results are tracked in [status](status.md).

| Existing records | New owner | Migration rule |
|---|---|---|
| `users`, `user_profiles`, `departments` | Identity | Preserve identifiers, hashes, role/active flags and timestamps |
| `courses`, `modules`, `lessons`, `course_skills` | Learning | Preserve curriculum, ordering, content, media and competency references |
| `enrollments`, `progress_records`, `planned_courses`, `learning_history`, `search_history` | Learning | Preserve progress and activity; do not infer new completion |
| `skills`, `user_skills` | Competency | Preserve legacy skill vocabulary/acquisition evidence alongside canonical mappings |
| `assessments`, `questions`, `assessment_attempts` | Assessment | Preserve IDs, keys and historical submitted/scored payloads |
| `competency_domains`, `competencies`, `competency_profiles`, `user_competency_scores`, `evidence_competency_mapping`, `gap_analyses`, `recommendations` | Competency | Preserve provenance, gap history and recommendation status |
| `stat_engine_questions`, `stat_engine_attempts`, `stat_engine_mastery` | Assessment | Preserve assessment-engine state; publish mapped evidence without overwriting history |
| `behavioural_session_results` | Assessment | Preserve final case/interview results and learner association |
| `generated_quizzes`, `generated_quiz_questions`, `quiz_attempts` | Assessment | Preserve source references, question answers and attempt history |
| `technical_transcripts` | Content | Preserve original/cleaned source and metadata |
| `technical_learning_objectives`, `technical_lab_templates`, `technical_generated_labs`, `technical_lab_solutions` | Assessment | Preserve exercise definitions and trusted/untrusted status |
| `technical_lab_validation_results` | Labs | Preserve historical execution observations with exercise references |
| `cyber_sandbox_templates`, `cyber_sandbox_challenges` | Assessment | Preserve challenge content and answer material server-side |
| `cyber_sandbox_sessions` | Labs | Preserve historical records; old host processes/ports are not migrated as live sessions |
| `user_cyber_competencies` | Competency | Preserve legacy scores with explicit historical provenance |
| Content-pipeline `fields`, `topics`, `resources` | Content | Preserve source URLs and taxonomy; these exist outside the original ORM inventory |

## Rules

- Reference a captured source revision and migration list. Never connect merely by inheriting root `.env`.
- Default to dry run. Applying requires explicit source and target URLs and an apply flag. Never log credentials.
- Require an empty migration destination or validated resumable state; never drop or overwrite existing target records silently.
- Copy parent records before dependent records, preserving IDs. Reset PostgreSQL sequences after copied integer IDs.
- External references become scalar identifiers, not cross-service foreign keys. Validate them during reconciliation.
- Report missing tables and unsupported records. Absence in a particular deployment is not permission to discard another source's data.
- Compare counts, IDs, critical fields and representative JSON payloads. Preserve UTF-8 explicitly.
- Do not convert historical LLM-derived scores into verified measurements. Keep the source and scoring version where available.
- Certificate presentation in the legacy app sometimes derives identifiers rather than storing a credential row. Preserve that identity and distinguish imported records from newly issued credentials.

## Cutover and rollback

Rehearse using a restored copy first. At actual cutover, stop source writes, take a verified backup, run the final migration and reconciliation, then switch application routing. Keep the old database unchanged. If validation fails before new writes, restore routing to the old application. Once new writes exist, rollback requires an explicit export/reconciliation of those writes rather than blindly repointing the frontend.
