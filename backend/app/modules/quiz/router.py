import json
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, GeneratedQuiz, GeneratedQuizQuestion, QuizAttempt
from app.agents.quiz.extract import extract_text, MAX_UPLOAD_BYTES
from app.agents.quiz.generator import generate_quiz_questions, DIFFICULTIES

router = APIRouter(prefix="/quiz", tags=["quiz"])

MIN_SOURCE_CHARS = 200


class SubmitQuizRequest(BaseModel):
    answers: Dict[int, int]  # question_id -> selected option index


def _can_manage(user: User, quiz: GeneratedQuiz) -> bool:
    return user.role == "admin" or quiz.user_id == user.id


def _get_quiz(db: Session, quiz_id: int) -> GeneratedQuiz:
    quiz = db.query(GeneratedQuiz).filter_by(id=quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


def _serialize_quiz(quiz: GeneratedQuiz, include_answers: bool) -> dict:
    questions = []
    for q in quiz.questions:
        item = {"id": q.id, "order": q.order, "question": q.question_text, "options": json.loads(q.options_json), "concept": q.concept}
        if include_answers:
            item["correct_index"] = q.correct_option_index
            item["explanation"] = q.explanation
        questions.append(item)
    return {
        "id": quiz.id,
        "title": quiz.title,
        "source_name": quiz.source_name,
        "source_type": quiz.source_type,
        "difficulty": quiz.difficulty,
        "generator": quiz.generator,
        "created_at": quiz.created_at.isoformat() if quiz.created_at else None,
        "creator_name": quiz.creator.full_name if quiz.creator else None,
        "can_manage": include_answers,
        "question_count": len(questions),
        "questions": questions,
    }


@router.post("/generate")
def generate_quiz(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    num_questions: int = Form(10),
    difficulty: str = Form("intermediate"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not 1 <= num_questions <= 30:
        raise HTTPException(status_code=400, detail="num_questions must be between 1 and 30")
    if difficulty not in DIFFICULTIES:
        raise HTTPException(status_code=400, detail=f"difficulty must be one of {sorted(DIFFICULTIES)}")
    if file is None and not (text and text.strip()):
        raise HTTPException(status_code=400, detail="Upload a learning material file or paste text")

    if file is not None:
        data = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File too large (max 20 MB)")
        try:
            content = extract_text(file.filename, data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            raise HTTPException(status_code=422, detail="Could not read the uploaded file. Is it corrupted or password protected?")
        source_name = file.filename
        source_type = Path(file.filename).suffix.lstrip(".").lower()
    else:
        content = text
        source_name = "Pasted text"
        source_type = "text"

    if len(content.strip()) < MIN_SOURCE_CHARS:
        raise HTTPException(status_code=422, detail="Not enough readable text to generate questions (need at least 200 characters)")

    questions, generator = generate_quiz_questions(content, num_questions, difficulty)
    if not questions:
        raise HTTPException(status_code=422, detail="Could not generate questions from this material")

    quiz = GeneratedQuiz(
        user_id=current_user.id,
        title=(title or "").strip() or f"Quiz: {Path(source_name).stem}",
        source_name=source_name,
        source_type=source_type,
        source_excerpt=content.strip()[:1000],
        difficulty=difficulty,
        generator=generator,
    )
    db.add(quiz)
    db.flush()
    for index, q in enumerate(questions, start=1):
        db.add(GeneratedQuizQuestion(
            quiz_id=quiz.id, order=index, question_text=q["question"], options_json=json.dumps(q["options"]),
            correct_option_index=q["correct_index"], explanation=q["explanation"], concept=q["concept"],
        ))
    db.commit()
    db.refresh(quiz)
    return _serialize_quiz(quiz, include_answers=True)


@router.get("")
def list_quizzes(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Eager load so the list is three queries, not two extra round trips per quiz.
    quizzes = (
        db.query(GeneratedQuiz)
        .options(selectinload(GeneratedQuiz.questions), selectinload(GeneratedQuiz.creator))
        .order_by(GeneratedQuiz.created_at.desc())
        .all()
    )
    my_attempts = db.query(QuizAttempt).filter_by(user_id=current_user.id).all()
    best = {}
    for attempt in my_attempts:
        best[attempt.quiz_id] = max(best.get(attempt.quiz_id, 0.0), attempt.score_percent)
    return [
        {
            "id": q.id, "title": q.title, "source_name": q.source_name, "source_type": q.source_type,
            "difficulty": q.difficulty, "generator": q.generator, "question_count": len(q.questions),
            "created_at": q.created_at.isoformat() if q.created_at else None,
            "creator_name": q.creator.full_name if q.creator else None,
            "can_manage": _can_manage(current_user, q), "best_score": best.get(q.id),
        }
        for q in quizzes
    ]


@router.get("/{quiz_id}")
def get_quiz(quiz_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    quiz = _get_quiz(db, quiz_id)
    return _serialize_quiz(quiz, include_answers=_can_manage(current_user, quiz))


@router.post("/{quiz_id}/submit")
def submit_quiz(
    quiz_id: int, req: SubmitQuizRequest,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db),
):
    quiz = _get_quiz(db, quiz_id)
    results = []
    correct_count = 0
    concepts_to_review = []
    for q in quiz.questions:
        selected = req.answers.get(q.id)
        is_correct = selected == q.correct_option_index
        correct_count += int(is_correct)
        if not is_correct and q.concept and q.concept not in concepts_to_review:
            concepts_to_review.append(q.concept)
        results.append({
            "question_id": q.id, "selected_index": selected, "correct_index": q.correct_option_index,
            "is_correct": is_correct, "explanation": q.explanation, "concept": q.concept,
        })

    total = len(quiz.questions)
    score = round(100.0 * correct_count / total, 1) if total else 0.0
    if score >= 85:
        band, message = "Excellent", "Strong command of this material. Try an advanced quiz next."
    elif score >= 60:
        band, message = "Proficient", "Good grasp overall. Review the explanations for the questions you missed."
    else:
        band, message = "Needs review", "Revisit the source material, focusing on the concepts listed below, then retake the quiz."

    attempt = QuizAttempt(
        quiz_id=quiz.id, user_id=current_user.id, answers_json=json.dumps({str(k): v for k, v in req.answers.items()}),
        correct_count=correct_count, total_questions=total, score_percent=score,
    )
    db.add(attempt)
    db.commit()

    # Real-time Attentive Knowledge Tracing (AKT) trigger
    try:
        from app.agents.competency.knowledge_tracing import AttentiveKnowledgeTracingEngine
        AttentiveKnowledgeTracingEngine.compute_mastery_and_gaps(db, current_user.id)
        AttentiveKnowledgeTracingEngine.generate_intelligent_recommendations(db, current_user.id)
    except Exception:
        pass

    return {
        "attempt_id": attempt.id, "score_percent": score, "correct_count": correct_count, "total_questions": total,
        "band": band, "feedback": message, "concepts_to_review": concepts_to_review, "results": results,
    }


@router.get("/{quiz_id}/attempts")
def list_attempts(quiz_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    _get_quiz(db, quiz_id)
    attempts = db.query(QuizAttempt).filter_by(quiz_id=quiz_id, user_id=current_user.id).order_by(QuizAttempt.submitted_at.desc()).all()
    return [
        {"id": a.id, "score_percent": a.score_percent, "correct_count": a.correct_count,
         "total_questions": a.total_questions, "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None}
        for a in attempts
    ]


@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    quiz = _get_quiz(db, quiz_id)
    if not _can_manage(current_user, quiz):
        raise HTTPException(status_code=403, detail="Only the quiz creator or an administrator can delete this quiz")
    db.delete(quiz)
    db.commit()
    return {"success": True}
