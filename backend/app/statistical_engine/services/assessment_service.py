import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from app.statistical_engine.core.exceptions import AttemptNotFoundException
from app.statistical_engine.competency.graph import competency_graph
from app.statistical_engine.competency.mastery import mastery_evaluator
from app.statistical_engine.questions.generator import question_generator, QuestionInternalRecord
from app.statistical_engine.questions.branching import branching_engine
from app.statistical_engine.questions.personalization import personalization_engine
from sqlalchemy.orm import Session
from app.statistical_engine.repositories.sql_repositories import (
    SQLQuestionRepository,
    SQLAttemptRepository,
    SQLLearnerRepository,
)
from app.statistical_engine.schemas.questions import (
    QuestionInstance,
    QuestionType,
    QuestionDifficulty,
    AnswerSubmissionResponse,
    FeedbackSchema,
    MasterySnapshot,
    NextActionSchema
)

class AssessmentService:
    """
    Central orchestrator powering the adaptive assessment session flow.
    """

    def generate_question(
        self,
        db: Session,
        skill_id: str,
        difficulty: Optional[QuestionDifficulty] = None,
        question_type: Optional[QuestionType] = None,
        seed: Optional[int] = None
    ) -> QuestionInstance:
        question_repo = SQLQuestionRepository(db)
        client_instance, internal_record = question_generator.generate_question(
            skill_id=skill_id,
            difficulty=difficulty,
            question_type=question_type,
            seed=seed
        )
        # Store internal evaluation record
        question_repo.save_instance(internal_record)
        return client_instance

    def get_next_question(
        self,
        db: Session,
        user_id: str,
        competency_id: str = "price_statistics",
        preferred_skill_id: Optional[str] = None,
        current_difficulty: Optional[QuestionDifficulty] = None,
        question_type: Optional[QuestionType] = None,
    ) -> QuestionInstance:
        learner_repo = SQLLearnerRepository(db)
        competency = competency_graph.get_competency(competency_id)
        user_mastery = learner_repo.get_user_mastery(user_id)

        target_skill, diff = personalization_engine.select_skill_and_difficulty(
            competency_skills=competency.get("skills", []),
            learner_mastery=user_mastery,
            preferred_skill_id=preferred_skill_id,
            requested_difficulty=current_difficulty
        )

        # A visual-question request must resolve to a skill that actually has a
        # chart template. This keeps the adaptive endpoint deterministic while
        # allowing the portal to deliberately practice graph interpretation.
        if question_type:
            compatible_skills = [
                skill["id"]
                for skill in competency.get("skills", [])
                if question_generator.find_templates_by_skill(skill["id"], question_type=question_type)
            ]
            if compatible_skills:
                target_skill = preferred_skill_id if preferred_skill_id in compatible_skills else compatible_skills[0]

        return self.generate_question(db, skill_id=target_skill, difficulty=diff, question_type=question_type)

    def submit_answer(
        self,
        db: Session,
        user_id: str,
        question_id: str,
        submitted_answer: Union[str, float, int],
        time_taken_seconds: Optional[int] = None
    ) -> AnswerSubmissionResponse:
        question_repo = SQLQuestionRepository(db)
        attempt_repo = SQLAttemptRepository(db)
        learner_repo = SQLLearnerRepository(db)

        record = question_repo.get_instance(question_id)
        if not record:
            raise AttemptNotFoundException(question_id)

        is_correct = False
        misconception_id: Optional[str] = None

        if record.question_type in (QuestionType.MCQ, QuestionType.CHART_INTERPRETATION):
            sub_str = str(submitted_answer).strip().upper()
            if sub_str == record.correct_option_id:
                is_correct = True
            else:
                # Check if submitted matching option text or ID
                opt_info = record.options_map.get(sub_str)
                if opt_info:
                    misconception_id = opt_info[1]
                else:
                    # Check by text
                    for opt_id, (val, mis_id) in record.options_map.items():
                        if str(val).strip() == str(submitted_answer).strip():
                            if opt_id == record.correct_option_id:
                                is_correct = True
                            else:
                                misconception_id = mis_id
                            break
        else:
            # Numeric evaluation with tolerance
            try:
                sub_num = float(submitted_answer)
                correct_num = float(record.correct_answer)
                if math.isfinite(sub_num) and abs(sub_num - correct_num) <= record.tolerance:
                    is_correct = True
            except Exception:
                is_correct = False

        score = 1.0 if is_correct else 0.0

        # Retrieve and update learner mastery
        user_mastery_map = learner_repo.get_user_mastery(user_id)
        current_skill_mastery = user_mastery_map.get(record.skill_id)

        updated_mastery = mastery_evaluator.update_mastery(
            current_mastery=current_skill_mastery,
            skill_id=record.skill_id,
            correct=is_correct,
            score_weight=score,
            misconception_id=misconception_id
        )

        # Persist updated mastery
        learner_repo.update_user_skill_mastery(
            user_id=user_id,
            skill_id=record.skill_id,
            mastery_data=updated_mastery.model_dump()
        )

        # Record attempt
        attempt_record = {
            "attempt_id": f"att-{datetime.now(timezone.utc).timestamp()}",
            "user_id": user_id,
            "question_id": question_id,
            "skill_id": record.skill_id,
            "submitted_answer": submitted_answer,
            "is_correct": is_correct,
            "score": score,
            "misconception_id": misconception_id,
            "time_taken_seconds": time_taken_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        attempt_repo.record_attempt(attempt_record)

        # Determine next action via Branching Engine
        user_attempts = attempt_repo.get_user_attempts(user_id, skill_id=record.skill_id)
        recent_errors = 0
        for att in reversed(user_attempts[-3:]):
            if not att.get("is_correct"):
                recent_errors += 1
            else:
                break

        next_action = branching_engine.evaluate(
            skill_id=record.skill_id,
            correct=is_correct,
            misconception_id=misconception_id,
            consecutive_errors=recent_errors,
            mastery_score=updated_mastery.score
        )

        # If next action is to serve a question, generate its ID
        if next_action.type in ("question", "remediation"):
            target_skill = next_action.target_skill_id or record.skill_id
            next_q = self.generate_question(db, skill_id=target_skill)
            next_action.question_id = next_q.question_id

        return AnswerSubmissionResponse(
            question_id=question_id,
            correct=is_correct,
            score=score,
            feedback=FeedbackSchema(
                explanation=record.explanation,
                misconception_id=misconception_id,
                correct_answer=record.correct_answer
            ),
            mastery=MasterySnapshot(
                skill_id=record.skill_id,
                score=updated_mastery.score,
                level=updated_mastery.level
            ),
            next=next_action
        )

assessment_service = AssessmentService()
