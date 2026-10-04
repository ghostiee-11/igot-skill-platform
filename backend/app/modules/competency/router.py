from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import (
    User, CompetencyProfile, GapAnalysis, CompetencyDomain, Competency, UserCompetencyScore, Course, Recommendation,
)
from app.agents.competency.knowledge_tracing import AttentiveKnowledgeTracingEngine
from app.agents.igot.client import domain_category_filter
from .schemas import GapAnalysisResponse, CompetencyProfileSchema, DomainGapSchema, TraceableProfileResponse

router = APIRouter(prefix="/competency", tags=["competency"])


@router.get("/domains/{domain_code}")
def get_domain_detail(
    domain_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    domain = db.query(CompetencyDomain).filter_by(code=domain_code).first()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competency domain not found")

    traceable = AttentiveKnowledgeTracingEngine.get_full_traceable_profile(db, current_user.id)
    domain_comps = [c for c in traceable["competencies"] if c["domain_code"] == domain_code]

    latest_gap = next((d for d in traceable["domains"] if d["code"] == domain_code), None)
    target_level = latest_gap["target_level"] if latest_gap else traceable["target_level"]
    current_level = latest_gap["current_level"] if latest_gap else 0.0
    gap_value = latest_gap["gap"] if latest_gap else 0.0

    recommendations = {
        r.course_id: r for r in db.query(Recommendation).filter_by(user_id=current_user.id).all() if r.course_id
    }
    courses = []
    for course in db.query(Course).filter(domain_category_filter(domain.code)).all():
        rec = recommendations.get(course.id)
        courses.append({
            "id": course.id,
            "title": course.title,
            "overview": course.overview,
            "difficulty": course.difficulty,
            "duration_hours": course.duration_hours,
            "category": course.category,
            "recommended": bool(rec and rec.status != "dismissed"),
            "reason": rec.reason if rec else None,
        })
    courses.sort(key=lambda c: not c["recommended"])

    return {
        "domain": {"code": domain.code, "name": domain.name, "description": domain.description},
        "target_level": target_level,
        "current_level": current_level,
        "gap": gap_value,
        "analyzed_at": traceable["last_traced_at"],
        "competencies": domain_comps,
        "courses": courses,
        "is_default_framework": True,
    }


def _serialize_gap(gap: GapAnalysis) -> DomainGapSchema:
    return DomainGapSchema(
        domain_code=gap.domain.code,
        domain_name=gap.domain.name,
        target_level=gap.target_level,
        current_level=gap.current_level,
        gap=gap.gap,
        generated_at=gap.generated_at.isoformat() if gap.generated_at else "",
    )


@router.post("/analyze", response_model=GapAnalysisResponse)
def analyze_competency(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Executes full Attentive Knowledge Tracing (AKT), recomputes topic mastery,
    derives skill gaps against role targets, and regenerates smart recommendations.
    """
    result = AttentiveKnowledgeTracingEngine.compute_mastery_and_gaps(db, current_user.id)
    AttentiveKnowledgeTracingEngine.generate_intelligent_recommendations(db, current_user.id)

    profile = result["profile"]
    return GapAnalysisResponse(
        profile=CompetencyProfileSchema(
            statistical_score=profile.statistical_score,
            technical_score=profile.technical_score,
            digital_governance_score=profile.digital_governance_score,
            behavioural_score=profile.behavioural_score,
            last_computed_at=profile.last_computed_at.isoformat() if profile.last_computed_at else None,
        ),
        gaps=[_serialize_gap(g) for g in result["gaps"]],
        target_level=result["target_level"],
        overall_average_level=round(
            sum(result["computed_levels"].values()) / max(len(result["computed_levels"]), 1), 2
        ),
    )


@router.get("/traceable", response_model=TraceableProfileResponse)
def get_traceable_knowledge_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Returns granular competency mastery scores with evidence history
    and Strong / Developing / Gap classifications.
    """
    return AttentiveKnowledgeTracingEngine.get_full_traceable_profile(db, current_user.id)


@router.get("/profile", response_model=CompetencyProfileSchema)
def get_competency_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    profile = db.query(CompetencyProfile).filter_by(user_id=current_user.id).first()
    if not profile:
        # Run AKT on demand if no profile exists yet
        result = AttentiveKnowledgeTracingEngine.compute_mastery_and_gaps(db, current_user.id)
        profile = result["profile"]

    return CompetencyProfileSchema(
        statistical_score=profile.statistical_score,
        technical_score=profile.technical_score,
        digital_governance_score=profile.digital_governance_score,
        behavioural_score=profile.behavioural_score,
        last_computed_at=profile.last_computed_at.isoformat() if profile.last_computed_at else None,
    )


@router.get("/gaps", response_model=list[DomainGapSchema])
def get_competency_gaps(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    all_rows = db.query(GapAnalysis).filter_by(user_id=current_user.id).order_by(GapAnalysis.generated_at.desc()).all()
    if not all_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No competency gap analysis found for this learner. Run /analyze first."
        )

    latest_by_domain = {}
    for row in all_rows:
        if row.domain_id not in latest_by_domain:
            latest_by_domain[row.domain_id] = row

    return [_serialize_gap(g) for g in latest_by_domain.values()]
