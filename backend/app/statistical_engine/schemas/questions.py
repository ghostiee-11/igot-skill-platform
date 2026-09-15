from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from app.statistical_engine.schemas.charts import ChartSpec

class QuestionType(str, Enum):
    NUMERIC = "numeric"
    MCQ = "mcq"
    CHART_INTERPRETATION = "chart_interpretation"
    TRUE_FALSE = "true_false"

class QuestionDifficulty(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class MCQOption(BaseModel):
    id: str
    text: str

class QuestionInstance(BaseModel):
    """Client-facing representation. Note: correct answer is strictly withheld."""
    question_id: str
    skill_id: str
    competency_id: str
    type: QuestionType
    difficulty: QuestionDifficulty
    prompt: str
    data: Dict[str, Any] = Field(default_factory=dict)
    options: Optional[List[MCQOption]] = None
    chart: Optional[ChartSpec] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QuestionGenerateRequest(BaseModel):
    skill_id: str
    difficulty: Optional[QuestionDifficulty] = QuestionDifficulty.BASIC
    question_type: Optional[QuestionType] = None
    seed: Optional[int] = None

class NextQuestionRequest(BaseModel):
    user_id: str
    competency_id: str = "price_statistics"
    preferred_skill_id: Optional[str] = None
    current_difficulty: Optional[QuestionDifficulty] = None
    question_type: Optional[QuestionType] = None

class SubmitAnswerRequest(BaseModel):
    user_id: str
    question_id: str
    submitted_answer: Union[str, float, int]
    time_taken_seconds: Optional[int] = None

class FeedbackSchema(BaseModel):
    explanation: str
    misconception_id: Optional[str] = None
    correct_answer: Optional[Union[str, float, int]] = None

class MasterySnapshot(BaseModel):
    skill_id: str
    score: float
    level: str

class NextActionSchema(BaseModel):
    type: str # "question", "remediation", "competency_complete"
    question_id: Optional[str] = None
    target_skill_id: Optional[str] = None
    message: Optional[str] = None

class AnswerSubmissionResponse(BaseModel):
    question_id: str
    correct: bool
    score: float
    feedback: FeedbackSchema
    mastery: MasterySnapshot
    next: NextActionSchema
