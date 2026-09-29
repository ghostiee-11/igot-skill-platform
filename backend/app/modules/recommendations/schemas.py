from typing import Optional
from pydantic import BaseModel, ConfigDict


class RecommendationSchema(BaseModel):
    id: int
    course_id: Optional[int] = None
    course_title: Optional[str] = None
    reason: str
    score: float
    status: str
    generated_at: str
    type: Optional[str] = "course"
    category: Optional[str] = None
    difficulty: Optional[str] = None
    duration: Optional[str] = None
    target_competency: Optional[str] = None
    href: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
