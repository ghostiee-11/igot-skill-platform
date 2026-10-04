import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="learner")  # "learner" or "admin"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    assessment_attempts = relationship("AssessmentAttempt", back_populates="user", cascade="all, delete-orphan")
    planned_courses = relationship("PlannedCourse", back_populates="user", cascade="all, delete-orphan")
    learning_history = relationship("LearningHistory", back_populates="user", cascade="all, delete-orphan")
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    cyber_sessions = relationship("CyberSandboxSession", back_populates="user", cascade="all, delete-orphan")
    cyber_competency = relationship("UserCyberCompetency", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Onboarding step 3: Education / Work Experience / Previous Training
    education = Column(String(255), nullable=True)
    work_experience_years = Column(Integer, default=0)
    prior_training = Column(Text, nullable=True)
    
    # Onboarding step 4: Designation / Department / Job Role
    designation = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    job_role = Column(String(255), nullable=True)
    
    # Onboarding step 5: Current Assignment / Areas of Interest
    current_assignment = Column(Text, nullable=True)
    areas_of_interest = Column(Text, nullable=True)  # Comma-separated or JSON string
    
    language_pref = Column(String(20), default="en")  # "en" or "hi"
    appearance_pref = Column(String(20), default="light")  # "light" or "dark"
    profile_pic_url = Column(String(500), nullable=True)
    onboarding_completed = Column(Boolean, default=False)
    
    daily_goal_minutes = Column(Integer, default=30)
    current_streak_days = Column(Integer, default=1)
    last_active_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="profile")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    overview = Column(Text, nullable=False)
    instructor = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=False)  # e.g., MoSPI, CSO, ISTM
    duration_hours = Column(Float, default=4.0)
    difficulty = Column(String(50), default="intermediate")  # beginner, intermediate, advanced
    source = Column(String(50), default="internal")  # internal, external
    category = Column(String(100), default="General", index=True)
    thumbnail_url = Column(String(500), nullable=True)
    rating = Column(Float, default=4.8)
    enrolled_count = Column(Integer, default=0)
    is_popular = Column(Boolean, default=False)
    is_new = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order")
    course_skills = relationship("CourseSkill", back_populates="course", cascade="all, delete-orphan")
    assessment = relationship("Assessment", back_populates="course", uselist=False, cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=1)

    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan", order_by="Lesson.order")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    topic = Column(String(100), nullable=True)
    learning_objective = Column(Text, nullable=True)
    content_type = Column(String(50), default="reading")  # video, reading, lab
    duration_minutes = Column(Integer, default=15)
    content = Column(Text, nullable=False)  # Markdown text or video transcript
    video_url = Column(String(500), nullable=True)
    video_start_time = Column(Integer, default=0, nullable=True)  # Start timestamp in seconds
    video_end_time = Column(Integer, nullable=True)  # End timestamp in seconds
    source_video_title = Column(String(255), nullable=True)  # Curated source lecture title
    
    # In-lesson Practice Activity (per Section 4.3 conflict #4)
    activity_question = Column(Text, nullable=True)
    activity_options_json = Column(Text, nullable=True)  # JSON array of strings
    activity_correct_option = Column(Integer, nullable=True)  # 0-indexed
    activity_explanation = Column(Text, nullable=True)
    
    order = Column(Integer, default=1)

    module = relationship("Module", back_populates="lessons")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), default="Technical")

    course_skills = relationship("CourseSkill", back_populates="skill")
    user_skills = relationship("UserSkill", back_populates="skill")


class CourseSkill(Base):
    __tablename__ = "course_skills"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)

    course = relationship("Course", back_populates="course_skills")
    skill = relationship("Skill", back_populates="course_skills")


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    source_course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    competency_id = Column(Integer, ForeignKey("competencies.id", ondelete="SET NULL"), nullable=True)
    acquired_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")
    source_course = relationship("Course")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="in_progress")  # in_progress, completed
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    progress_percent = Column(Float, default=0.0)
    last_lesson_id = Column(Integer, nullable=True)

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    progress_records = relationship("Progress", back_populates="enrollment", cascade="all, delete-orphan")


class Progress(Base):
    __tablename__ = "progress_records"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, nullable=False)
    lesson_id = Column(Integer, nullable=False)
    completed = Column(Boolean, default=True)
    activity_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    enrollment = relationship("Enrollment", back_populates="progress_records")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    time_limit_minutes = Column(Integer, default=30)
    pass_threshold_percent = Column(Float, default=70.0)

    course = relationship("Course", back_populates="assessment")
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan", order_by="Question.order")
    attempts = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)  # JSON array of strings
    correct_option_index = Column(Integer, nullable=False)  # 0, 1, 2, 3
    explanation = Column(Text, nullable=True)
    order = Column(Integer, default=1)

    assessment = relationship("Assessment", back_populates="questions")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    score_percent = Column(Float, nullable=False)
    passed = Column(Boolean, nullable=False)
    answers_json = Column(Text, nullable=False)  # JSON object {question_id: selected_index}
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="assessment_attempts")
    assessment = relationship("Assessment", back_populates="attempts")


class PlannedCourse(Base):
    __tablename__ = "planned_courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    planned_for = Column(String(100), nullable=True)  # e.g., "Next Month" or date
    source = Column(String(50), default="self")  # "self" or "admin"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="planned_courses")
    course = relationship("Course")


class LearningHistory(Base):
    __tablename__ = "learning_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="learning_history")
    course = relationship("Course")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query = Column(String(255), nullable=False)
    searched_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="search_history")


# ============================================================================
# TECHNICAL COURSE CONTENT GENERATION PIPELINE MODELS
# ============================================================================

class TechnicalTranscript(Base):
    __tablename__ = "technical_transcripts"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=False)
    chunks_json = Column(Text, nullable=False)  # JSON list of chunks with metadata
    metadata_json = Column(Text, nullable=True)  # JSON dict with token_count, source, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    learning_objectives = relationship("TechnicalLearningObjective", back_populates="transcript", cascade="all, delete-orphan")


class TechnicalLearningObjective(Base):
    __tablename__ = "technical_learning_objectives"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("technical_transcripts.id", ondelete="CASCADE"), nullable=True)
    objective = Column(Text, nullable=False)
    skill = Column(String(255), nullable=False, index=True)
    difficulty = Column(String(50), default="intermediate")  # beginner, intermediate, advanced
    action_verb = Column(String(100), nullable=False)  # implement, debug, analyze, configure, etc.
    assessment_mode = Column(String(50), default="lab")  # lab or quiz
    suitability_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transcript = relationship("TechnicalTranscript", back_populates="learning_objectives")
    generated_labs = relationship("TechnicalGeneratedLab", back_populates="learning_objective")


class TechnicalLabTemplate(Base):
    __tablename__ = "technical_lab_templates"

    id = Column(String(100), primary_key=True, index=True)  # Human-created template identifier
    title = Column(String(255), nullable=False)
    skill = Column(String(255), nullable=False, index=True)  # e.g., "FastAPI", "Pandas", "Python", "SQL"
    language = Column(String(50), default="python", index=True)  # python, sql, bash, etc.
    difficulty = Column(String(50), default="intermediate")  # beginner, intermediate, advanced
    lab_type = Column(String(100), default="implementation")  # implementation, debugging, data_analysis, refactoring
    tags_json = Column(Text, default="[]")  # JSON list of string tags for matching
    instructions_template = Column(Text, nullable=False)
    starter_code_template = Column(Text, nullable=False)
    solution_template = Column(Text, nullable=True)
    constraints_json = Column(Text, default="[]")  # JSON list of constraint strings
    test_cases_template_json = Column(Text, default="[]")  # JSON list of test case specs
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    generated_labs = relationship("TechnicalGeneratedLab", back_populates="template")


class TechnicalGeneratedLab(Base):
    __tablename__ = "technical_generated_labs"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(100), ForeignKey("technical_lab_templates.id", ondelete="SET NULL"), nullable=True)
    objective_id = Column(Integer, ForeignKey("technical_learning_objectives.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    language = Column(String(50), default="python")
    difficulty = Column(String(50), default="intermediate")
    instructions = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=False)
    constraints_json = Column(Text, default="[]")  # JSON list of string constraints
    test_cases_json = Column(Text, default="[]")  # JSON list of test case dicts
    expected_behavior = Column(Text, nullable=True)
    status = Column(String(50), default="draft")  # draft, pending_validation, validated, rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    template = relationship("TechnicalLabTemplate", back_populates="generated_labs")
    learning_objective = relationship("TechnicalLearningObjective", back_populates="generated_labs")
    solution = relationship("TechnicalLabSolution", back_populates="lab", uselist=False, cascade="all, delete-orphan")
    validation_results = relationship("TechnicalLabValidationResult", back_populates="lab", cascade="all, delete-orphan")


class TechnicalLabSolution(Base):
    __tablename__ = "technical_lab_solutions"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("technical_generated_labs.id", ondelete="CASCADE"), unique=True, nullable=False)
    reference_code = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lab = relationship("TechnicalGeneratedLab", back_populates="solution")


class TechnicalLabValidationResult(Base):
    __tablename__ = "technical_lab_validation_results"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("technical_generated_labs.id", ondelete="CASCADE"), nullable=False)
    solution_id = Column(Integer, ForeignKey("technical_lab_solutions.id", ondelete="SET NULL"), nullable=True)
    is_valid = Column(Boolean, default=False, nullable=False)
    sandbox_type = Column(String(50), default="docker")  # docker or subprocess-dev-fallback
    exit_code = Column(Integer, default=0)
    execution_time_ms = Column(Float, default=0.0)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    test_summary_json = Column(Text, nullable=True)  # JSON summary of individual test cases
    error_message = Column(Text, nullable=True)
    validated_at = Column(DateTime, default=datetime.datetime.utcnow)

    lab = relationship("TechnicalGeneratedLab", back_populates="validation_results")

# ============================================================================
# DIGITAL GOVERNANCE & CYBERSECURITY SANDBOX MODELS
# ============================================================================

class CyberSandboxTemplate(Base):
    __tablename__ = "cyber_sandbox_templates"

    id = Column(String(100), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    difficulty = Column(String(50), default="intermediate")
    competency_id = Column(String(100), default="soc_investigation")
    points = Column(Integer, default=100)
    duration_minutes = Column(Integer, default=45)
    tags_json = Column(Text, default="[]")
    mitre_techniques_json = Column(Text, default="[]")
    scenario_template = Column(Text, nullable=False)
    instructions_template = Column(Text, nullable=False)
    hints_template_json = Column(Text, default="[]")
    artifacts_spec_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    challenges = relationship("CyberSandboxChallenge", back_populates="template")


class CyberSandboxChallenge(Base):
    __tablename__ = "cyber_sandbox_challenges"

    id = Column(String(100), primary_key=True, index=True)
    template_id = Column(String(100), ForeignKey("cyber_sandbox_templates.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    difficulty = Column(String(50), default="intermediate")
    points = Column(Integer, default=100)
    duration_minutes = Column(Integer, default=45)
    competency_id = Column(String(100), default="soc_investigation")
    is_flagship = Column(Boolean, default=False)
    tags_json = Column(Text, default="[]")
    mitre_techniques_json = Column(Text, default="[]")
    objectives_json = Column(Text, default="[]")
    scenario_markdown = Column(Text, nullable=False)
    flag = Column(String(255), nullable=False)
    hints_json = Column(Text, default="[]")
    artifacts_json = Column(Text, default="{}")
    notebook_code = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    template = relationship("CyberSandboxTemplate", back_populates="challenges")
    sessions = relationship("CyberSandboxSession", back_populates="challenge", cascade="all, delete-orphan")


class CyberSandboxSession(Base):
    __tablename__ = "cyber_sandbox_sessions"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    challenge_id = Column(String(100), ForeignKey("cyber_sandbox_challenges.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="running")
    assigned_port = Column(Integer, nullable=False)
    flag = Column(String(255), nullable=False)
    unlocked_hints_json = Column(Text, default="[]")
    total_penalties = Column(Integer, default=0)
    final_score = Column(Integer, default=0)
    is_solved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    solved_at = Column(DateTime, nullable=True)

    challenge = relationship("CyberSandboxChallenge", back_populates="sessions")
    user = relationship("User", back_populates="cyber_sessions")


class UserCyberCompetency(Base):
    __tablename__ = "user_cyber_competencies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    soc_investigation = Column(Integer, default=0)
    phishing_analysis = Column(Integer, default=0)
    cloud_security = Column(Integer, default=0)
    dpi_security = Column(Integer, default=0)
    digital_forensics = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    solved_challenges_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="cyber_competency")


class CompetencyDomain(Base):
    __tablename__ = "competency_domains"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    competencies = relationship("Competency", back_populates="domain", cascade="all, delete-orphan")


class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("competency_domains.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    max_level = Column(Integer, default=5)

    domain = relationship("CompetencyDomain", back_populates="competencies")


class CompetencyProfile(Base):
    __tablename__ = "competency_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    statistical_score = Column(Float, default=0.0)
    technical_score = Column(Float, default=0.0)
    digital_governance_score = Column(Float, default=0.0)
    behavioural_score = Column(Float, default=0.0)
    last_computed_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User")


class UserCompetencyScore(Base):
    __tablename__ = "user_competency_scores"
    __table_args__ = (
        UniqueConstraint("user_id", "competency_id", name="uq_user_competency"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False)
    level = Column(Float, default=0.0)  # 0-5
    evidence_source = Column(String(50), default="self_declared")  # self_declared, assessment, inferred
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User")
    competency = relationship("Competency")


class GapAnalysis(Base):
    __tablename__ = "gap_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    domain_id = Column(Integer, ForeignKey("competency_domains.id", ondelete="CASCADE"), nullable=False)
    target_level = Column(Float, nullable=False)
    current_level = Column(Float, nullable=False)
    gap = Column(Float, nullable=False)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
    domain = relationship("CompetencyDomain")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=False)
    score = Column(Float, default=0.0)
    status = Column(String(20), default="pending")  # pending, enrolled, dismissed
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
    course = relationship("Course")


class StatEngineQuestion(Base):
    __tablename__ = "stat_engine_questions"

    question_id = Column(String(100), primary_key=True)
    template_id = Column(String(100), nullable=False)
    skill_id = Column(String(100), nullable=False, index=True)
    competency_id = Column(String(100), nullable=False)
    question_type = Column(String(50), nullable=False)
    difficulty = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    parameters_json = Column(Text, nullable=False)
    correct_answer_json = Column(Text, nullable=False)
    tolerance = Column(Float, default=0.0)
    options_map_json = Column(Text, nullable=False)
    correct_option_id = Column(String(50), nullable=True)
    explanation = Column(Text, nullable=True)
    unit = Column(String(100), nullable=True)
    chart_json = Column(Text, nullable=True)
    seed = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class StatEngineAttempt(Base):
    __tablename__ = "stat_engine_attempts"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(String(100), nullable=False, index=True)
    question_id = Column(String(100), nullable=False)
    skill_id = Column(String(100), nullable=False, index=True)
    submitted_answer = Column(String(255), nullable=True)
    is_correct = Column(Boolean, default=False)
    score = Column(Float, default=0.0)
    misconception_id = Column(String(100), nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class StatEngineMastery(Base):
    __tablename__ = "stat_engine_mastery"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_stat_mastery_user_skill"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    skill_id = Column(String(100), nullable=False)
    mastery_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class BehaviouralSessionResult(Base):
    __tablename__ = "behavioural_session_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    session_type = Column(String(20), nullable=False)  # carryforward, interview
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    case_or_course_id = Column(String(100), nullable=True)
    score = Column(Float, default=0.0)
    result_json = Column(Text, nullable=False)
    completed_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User")


class EvidenceCompetencyMapping(Base):
    __tablename__ = "evidence_competency_mapping"
    __table_args__ = (
        UniqueConstraint("source_system", "source_key", name="uq_evidence_mapping_source"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(50), nullable=False)  # stat_engine_skill, stat_engine_competency, behavioural_competency
    source_key = Column(String(255), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False)

    competency = relationship("Competency")


class GeneratedQuiz(Base):
    __tablename__ = "generated_quizzes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(20), nullable=False)  # pdf, pptx, docx, txt, md, vtt, srt, text
    source_excerpt = Column(Text, nullable=True)
    difficulty = Column(String(20), default="intermediate")
    generator = Column(String(20), default="llm")  # llm, fallback
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("User")
    questions = relationship("GeneratedQuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="GeneratedQuizQuestion.order")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class GeneratedQuizQuestion(Base):
    __tablename__ = "generated_quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("generated_quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    order = Column(Integer, default=1)
    question_text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)
    correct_option_index = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    concept = Column(String(255), nullable=True)

    quiz = relationship("GeneratedQuiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("generated_quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answers_json = Column(Text, nullable=False)
    correct_count = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    score_percent = Column(Float, default=0.0)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    quiz = relationship("GeneratedQuiz", back_populates="attempts")
    user = relationship("User")

