import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, Recommendation, Enrollment, Course
from app.agents.competency.knowledge_tracing import AttentiveKnowledgeTracingEngine
from .schemas import RecommendationSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

RECOMMENDATION_STATUSES = {"pending", "enrolled", "dismissed"}


class RecommendationStatusUpdate(BaseModel):
    status: str


@router.patch("/{recommendation_id}", response_model=RecommendationSchema)
def update_recommendation_status(
    recommendation_id: int,
    req: RecommendationStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if req.status not in RECOMMENDATION_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(RECOMMENDATION_STATUSES)}")
    rec = db.query(Recommendation).filter_by(id=recommendation_id, user_id=current_user.id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.status = req.status
    if req.status == "enrolled" and rec.course_id:
        if not db.query(Enrollment).filter_by(user_id=current_user.id, course_id=rec.course_id).first():
            db.add(Enrollment(user_id=current_user.id, course_id=rec.course_id, status="in_progress"))
    db.commit()
    db.refresh(rec)
    return _serialize(rec)


@router.post("/generate", response_model=list[RecommendationSchema])
def generate_user_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generates intelligent recommendations mapped to AKT skill gaps and uncompleted material."""
    raw_recs = AttentiveKnowledgeTracingEngine.generate_intelligent_recommendations(db, current_user.id)
    return [_serialize_dict_or_model(r) for r in raw_recs]


@router.get("", response_model=list[RecommendationSchema])
def list_user_recommendations(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(Recommendation).options(joinedload(Recommendation.course)).filter_by(user_id=current_user.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    rows = query.order_by(Recommendation.generated_at.desc()).all()

    if not rows and (status_filter is None or status_filter == "pending"):
        # Auto-generate if empty
        raw_recs = AttentiveKnowledgeTracingEngine.generate_intelligent_recommendations(db, current_user.id)
        return [_serialize_dict_or_model(r) for r in raw_recs]

    return [_serialize(r) for r in rows]


def _serialize(r: Recommendation) -> RecommendationSchema:
    course = r.course
    return RecommendationSchema(
        id=r.id,
        course_id=r.course_id,
        course_title=course.title if course else "Targeted Learning Unit",
        reason=r.reason,
        score=r.score,
        status=r.status,
        generated_at=r.generated_at.isoformat() if r.generated_at else "",
        type="course",
        category=course.category if course else "General",
        difficulty=course.difficulty if course else "intermediate",
        duration=f"{course.duration_hours:g} hours" if course else "2 hours",
        target_competency=course.category if course else "Core Competency",
        href=f"/courses/{course.id}" if course else "/courses",
    )


def _serialize_dict_or_model(item: Any) -> RecommendationSchema:
    if isinstance(item, dict):
        return RecommendationSchema(
            id=item.get("id", 1),
            course_id=item.get("item_id") if isinstance(item.get("item_id"), int) else None,
            course_title=item.get("title"),
            reason=item.get("reason", ""),
            score=item.get("score", 50.0),
            status=item.get("status", "pending"),
            generated_at=item.get("generated_at", ""),
            type=item.get("type", "course"),
            category=item.get("category"),
            difficulty=item.get("difficulty"),
            duration=item.get("duration"),
            target_competency=item.get("target_competency"),
            href=item.get("href"),
        )
    return _serialize(item)
