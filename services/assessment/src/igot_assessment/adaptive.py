"""Persisted adaptive practice over the imported statistical item bank."""

import math
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import StatEngineAttempt, StatEngineMastery, StatEngineQuestion


def level(score: float) -> str:
    if score >= 90: return "master"
    if score >= 75: return "advanced"
    if score >= 50: return "intermediate"
    if score >= 25: return "basic"
    return "novice"


def public_question(question: StatEngineQuestion) -> dict:
    # Imported parameters include the answer used to instantiate the template.
    data = {key: value for key, value in (question.parameters or {}).items() if key.lower() not in {"answer", "correct_answer"}}
    return {"question_id": question.question_id, "skill_id": question.skill_id,
            "competency_id": question.competency_id, "type": question.question_type,
            "difficulty": question.difficulty, "prompt": question.prompt, "data": data,
            "options": [{"id": key, "text": str(value[0] if isinstance(value, list) else value)} for key, value in (question.options_map or {}).items()] or None,
            "chart": question.chart, "metadata": {"unit": question.unit} if question.unit else {}}


def next_question(db: Session, user_id: int, competency_id: str, preferred_skill_id: str | None = None,
                  difficulty: str | None = None, question_type: str | None = None) -> dict:
    questions = db.scalars(select(StatEngineQuestion).where(StatEngineQuestion.competency_id == competency_id)).all()
    if not questions: raise HTTPException(404, "No questions are available for this competency")
    if question_type:
        questions = [q for q in questions if q.question_type == question_type]
    if not questions: raise HTTPException(404, "No questions are available in this format")
    mastery = {m.skill_id: m.score for m in db.scalars(select(StatEngineMastery).where(StatEngineMastery.user_id == user_id)).all()}
    attempts = {a.question_id for a in db.scalars(select(StatEngineAttempt).where(StatEngineAttempt.user_id == user_id)).all()}
    questions.sort(key=lambda q: (q.question_id in attempts, 0 if preferred_skill_id and q.skill_id == preferred_skill_id else 1,
                                  mastery.get(q.skill_id, 0), 0 if not difficulty or q.difficulty == difficulty else 1, q.question_id))
    return public_question(questions[0])


def submit_answer(db: Session, user_id: int, question_id: str, answer: str | float | int,
                  time_taken_seconds: int | None = None) -> dict:
    question = db.get(StatEngineQuestion, question_id)
    if not question: raise HTTPException(404, "Question not found")
    misconception = None
    if question.question_type in {"mcq", "chart_interpretation", "true_false"}:
        selected = str(answer).strip().upper()
        correct = selected == question.correct_option_id
        option = (question.options_map or {}).get(selected)
        if not correct and isinstance(option, list) and len(option) > 1: misconception = option[1]
    else:
        try:
            value = float(answer)
            correct = math.isfinite(value) and abs(value - float(question.correct_answer)) <= (question.tolerance if question.tolerance is not None else 0.5)
        except (TypeError, ValueError, OverflowError): correct = False
    mastery = db.scalar(select(StatEngineMastery).where(StatEngineMastery.user_id == user_id, StatEngineMastery.skill_id == question.skill_id))
    if not mastery:
        mastery = StatEngineMastery(user_id=user_id, skill_id=question.skill_id, score=0, attempts_count=0, correct_count=0, consecutive_errors=0)
        db.add(mastery)
    mastery.attempts_count += 1
    mastery.correct_count += int(correct)
    mastery.consecutive_errors = 0 if correct else mastery.consecutive_errors + 1
    mastery.score = min(100, mastery.score + 10) if correct else max(0, mastery.score - 5)
    db.add(StatEngineAttempt(user_id=user_id, question_id=question_id, skill_id=question.skill_id,
                             submitted_answer=str(answer), correct=correct, misconception_id=misconception,
                             time_taken_seconds=time_taken_seconds))
    db.commit()
    remediation = not correct and (mastery.consecutive_errors >= 2 or bool(misconception))
    target = question.skill_id
    if mastery.consecutive_errors >= 2:
        target = {"price.cpi.weighted_price_relatives": "price.price_relative",
                  "price.fisher_index": "price.laspeyres_index"}.get(question.skill_id, target)
    elif correct and mastery.score >= 80:
        target = {"price.price_relative": "price.weights", "price.weights": "price.cpi.weighted_price_relatives",
                  "price.cpi.weighted_price_relatives": "price.inflation_rate", "price.inflation_rate": "price.laspeyres_index",
                  "price.laspeyres_index": "price.paasche_index", "price.paasche_index": "price.fisher_index",
                  "price.fisher_index": "price.real_vs_nominal"}.get(question.skill_id, target)
    return {"question_id": question_id, "correct": correct, "score": 1.0 if correct else 0.0,
            "feedback": {"explanation": question.explanation or "Review the calculation and try again.",
                         "misconception_id": misconception, "correct_answer": question.correct_option_id if question.correct_option_id else question.correct_answer},
            "mastery": {"skill_id": question.skill_id, "score": mastery.score, "level": level(mastery.score)},
            "next": {"type": "remediation" if remediation else "question", "target_skill_id": target,
                     "message": "Review the underlying concept before continuing." if remediation else "Keep practicing to reinforce mastery."}}
