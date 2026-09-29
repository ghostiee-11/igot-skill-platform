from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class EvidenceItemSchema(BaseModel):
    title: str
    type: str
    score_pct: float
    date: str


class DomainCompetencySchema(BaseModel):
    id: Optional[int] = None
    code: str
    name: str
    level: float
    mastery_percent: Optional[float] = None
    target_level: Optional[float] = None
    gap: Optional[float] = None
    status: Optional[str] = None  # Strong, Developing, Gap
    status_color: Optional[str] = None
    evidence_source: Optional[str] = None
    evidence_count: Optional[int] = 0
    recent_evidence: Optional[List[EvidenceItemSchema]] = None


class DomainGapSchema(BaseModel):
    domain_code: str
    domain_name: str
    target_level: float
    current_level: float
    gap: float
    generated_at: str
    model_config = ConfigDict(from_attributes=True)


class CompetencyProfileSchema(BaseModel):
    statistical_score: float
    technical_score: float
    digital_governance_score: float
    behavioural_score: float
    last_computed_at: Optional[str] = None
    is_default_framework: bool = True
    model_config = ConfigDict(from_attributes=True)


class GapAnalysisResponse(BaseModel):
    profile: CompetencyProfileSchema
    gaps: List[DomainGapSchema]
    target_level: Optional[float] = 4.0
    overall_average_level: Optional[float] = 3.0


class TraceableProfileResponse(BaseModel):
    target_level: float
    overall_average_level: float
    domains: List[Dict[str, Any]]
    competencies: List[Dict[str, Any]]
    total_interactions_traced: int
    last_traced_at: str
