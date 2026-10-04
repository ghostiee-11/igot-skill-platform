from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import datetime


# ============================================================================
# TRANSCRIPT SCHEMAS
# ============================================================================

class TranscriptIngestRequest(BaseModel):
    title: str = Field(..., description="Title of the technical course or lecture")
    raw_text: str = Field(..., min_length=10, description="Raw transcript text or subtitle stream")
    course_id: Optional[int] = Field(None, description="Optional existing course ID to link to")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata such as duration, source, timestamps")


class TranscriptChunk(BaseModel):
    chunk_index: int
    text: str
    token_count: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptProcessResponse(BaseModel):
    id: Optional[int] = None
    title: str
    course_id: Optional[int] = None
    cleaned_length: int
    estimated_tokens: int
    chunk_count: int
    chunks: List[TranscriptChunk]
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# LEARNING OBJECTIVE SCHEMAS
# ============================================================================

class LearningObjectiveSchema(BaseModel):
    objective: str = Field(..., description="Concrete, actionable learning objective statement")
    skill: str = Field(..., description="Technical competency or library (e.g., FastAPI, Pandas, SQL)")
    difficulty: str = Field("intermediate", description="Difficulty level: beginner, intermediate, advanced")
    action: str = Field(..., description="Action verb (e.g., implement, debug, analyze, refactor, query)")
    assessment_mode: str = Field("lab", description="Appropriate assessment mode: 'lab' or 'quiz'")
    suitability_reason: Optional[str] = Field(None, description="Reasoning for choosing lab vs quiz")


class ObjectiveExtractionRequest(BaseModel):
    transcript_text: str = Field("", description="Cleaned transcript text to extract objectives from")
    transcript_id: Optional[int] = Field(None, description="Optional transcript ID for persistence")
    course_id: Optional[int] = Field(None, description="Optional course ID context")


class ObjectiveExtractionResponse(BaseModel):
    transcript_id: Optional[int] = None
    objectives: List[LearningObjectiveSchema]


# ============================================================================
# QUIZ VS LAB DECISION SCHEMAS
# ============================================================================

class DecisionRequest(BaseModel):
    objective: str
    skill: str
    action: Optional[str] = None
    difficulty: Optional[str] = "intermediate"


class DecisionResponse(BaseModel):
    assessment_mode: str = Field(..., description="'lab' for hands-on, 'quiz' for theoretical/recall")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    recommended_lab_type: Optional[str] = Field(None, description="implementation, debugging, data_analysis, refactoring")


# ============================================================================
# LAB TEMPLATE SCHEMAS (Human-Created)
# ============================================================================

class TestCaseSchema(BaseModel):
    __test__ = False
    name: str
    description: Optional[str] = None
    test_code: str = Field(..., description="Python assertion or test function code")
    is_hidden: bool = False
    weight: float = 1.0


class LabTemplateSchema(BaseModel):
    id: str = Field(..., description="Unique human-created template ID (e.g., 'python-fastapi-001')")
    title: str
    skill: str
    language: str = "python"
    difficulty: str = "intermediate"
    lab_type: str = "implementation"  # implementation, debugging, data_analysis, refactoring
    tags: List[str] = Field(default_factory=list)
    instructions_template: str
    starter_code_template: str
    solution_template: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    test_cases_template: List[TestCaseSchema] = Field(default_factory=list)


class TemplateMatchRequest(BaseModel):
    objective: str
    skill: str
    difficulty: Optional[str] = "intermediate"
    language: Optional[str] = "python"
    lab_type: Optional[str] = None


class TemplateMatchResponse(BaseModel):
    matched: bool
    template: Optional[LabTemplateSchema] = None
    match_score: float = 0.0
    match_reason: str


# ============================================================================
# LAB GENERATION SCHEMAS
# ============================================================================

class GeneratedLabSchema(BaseModel):
    title: str
    objective: str
    language: str = "python"
    difficulty: str = "intermediate"
    instructions: str
    starter_code: str
    constraints: List[str] = Field(default_factory=list)
    test_cases: List[TestCaseSchema] = Field(default_factory=list)
    expected_behavior: Optional[str] = None


class LabGenerationRequest(BaseModel):
    objective: LearningObjectiveSchema
    template_id: str
    course_context: Optional[str] = None
    persist: bool = True


class LabGenerationResponse(BaseModel):
    lab_id: Optional[int] = None
    template_id: str
    lab: GeneratedLabSchema
    status: str = "draft"


# ============================================================================
# SOLUTION GENERATION SCHEMAS
# ============================================================================

class SolutionGenerationRequest(BaseModel):
    lab_id: Optional[int] = None
    lab_schema: Optional[GeneratedLabSchema] = None
    persist: bool = True


class SolutionGenerationResponse(BaseModel):
    lab_id: Optional[int] = None
    solution_id: Optional[int] = None
    reference_code: str
    explanation: str
    is_trusted: bool = False  # False until validated in sandbox


# ============================================================================
# SANDBOX VALIDATION SCHEMAS
# ============================================================================

class SandboxExecutionRequest(BaseModel):
    code: str
    test_cases: List[TestCaseSchema]
    language: str = "python"
    timeout_seconds: int = 5
    memory_limit_mb: int = 128


class TestResultItem(BaseModel):
    name: str
    passed: bool
    error: Optional[str] = None
    duration_ms: float = 0.0


class ValidationResultSchema(BaseModel):
    is_valid: bool
    sandbox_type: str = "docker"  # "docker" or "subprocess-dev-fallback"
    exit_code: int
    execution_time_ms: float
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    test_results: List[TestResultItem] = Field(default_factory=list)
    passed_tests_count: int = 0
    total_tests_count: int = 0
    error_message: Optional[str] = None


class LabValidationResponse(BaseModel):
    lab_id: Any
    is_valid: bool
    status: str  # "validated" or "rejected"
    validation_details: ValidationResultSchema


# ============================================================================
# END-TO-END PIPELINE SCHEMAS
# ============================================================================

class FullPipelineRequest(BaseModel):
    transcript_text: str = Field(..., min_length=20)
    title: str = Field("Technical Module")
    course_id: Optional[int] = None
    preferred_language: str = "python"
    target_difficulty: Optional[str] = None


class FullPipelineResponse(BaseModel):
    success: bool
    transcript_id: Optional[int] = None
    objectives_count: int
    objectives: List[LearningObjectiveSchema]
    labs_generated_count: int
    validated_labs_count: int
    labs: List[Dict[str, Any]]
    execution_summary: Dict[str, Any]


# ============================================================================
# INTERACTIVE LAB EXECUTION & NOTEBOOK SCHEMAS
# ============================================================================

class ExecuteStudentCodeRequest(BaseModel):
    code: str = Field(..., description="Student code implementation to validate")


class ExecuteStudentCodeResponse(BaseModel):
    lab_id: Any
    all_passed: bool
    passed_tests_count: int
    total_tests_count: int
    test_results: List[TestResultItem]
    execution_time_ms: float
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: int
    feedback: Optional[str] = None


class ExecuteCellRequest(BaseModel):
    code: str = Field(..., description="Python cell code to execute")
    context_code: Optional[str] = Field(default="", description="Optional preceding context code")


class ExecuteCellResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_time_ms: float
    exit_code: int


class ExportNotebookRequest(BaseModel):
    title: str = Field("Karmayogi Lab Notebook", description="Title of the notebook")
    format: str = Field("marimo", description="'marimo' for Python app or 'ipynb' for Jupyter notebook")
    cells: List[Dict[str, Any]] = Field(default_factory=list, description="List of cell objects with type and content")


class ExportNotebookResponse(BaseModel):
    filename: str
    content: str
    format: str
    mime_type: str


class LabAssistantMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=2000)


class LabAssistantRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    current_code: str = Field(default="", max_length=20000)
    active_output: Optional[str] = Field(default=None, max_length=8000)
    history: List[LabAssistantMessage] = Field(default_factory=list, max_length=8)


class LabAssistantResponse(BaseModel):
    response: str
    source: str
    suggestions: List[str] = Field(default_factory=list)

