from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from .config import get_settings

SCHEMA="assessment"
class Base(DeclarativeBase): pass
class Assessment(Base):
    __tablename__="assessments"; __table_args__={"schema":SCHEMA}
    id: Mapped[int]=mapped_column(Integer,primary_key=True); course_id: Mapped[int]=mapped_column(Integer,index=True)
    title: Mapped[str]=mapped_column(String(250)); description: Mapped[str]=mapped_column(Text,default="")
    engine: Mapped[str]=mapped_column(String(40),default="course_quiz"); time_limit_minutes: Mapped[int]=mapped_column(Integer,default=30)
    pass_threshold_percent: Mapped[float]=mapped_column(Float,default=70); metadata_json: Mapped[dict]=mapped_column(JSON,default=dict)
    questions: Mapped[list["Question"]]=relationship(cascade="all, delete-orphan",order_by="Question.order")
class Question(Base):
    __tablename__="questions"; __table_args__={"schema":SCHEMA}
    id: Mapped[int]=mapped_column(Integer,primary_key=True); assessment_id: Mapped[int]=mapped_column(ForeignKey(f"{SCHEMA}.assessments.id",ondelete="CASCADE"),index=True)
    text: Mapped[str]=mapped_column(Text); options: Mapped[list]=mapped_column(JSON); correct_option_index: Mapped[int]=mapped_column(Integer)
    explanation: Mapped[str]=mapped_column(Text,default=""); competency_code: Mapped[str|None]=mapped_column(String(100),nullable=True); order: Mapped[int]=mapped_column(Integer,default=0)
class SessionRecord(Base):
    __tablename__="sessions"; __table_args__={"schema":SCHEMA}
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4())); user_id: Mapped[int]=mapped_column(Integer,index=True)
    assessment_id: Mapped[int|None]=mapped_column(Integer,nullable=True); engine: Mapped[str]=mapped_column(String(40)); status: Mapped[str]=mapped_column(String(30),default="active")
    state: Mapped[dict]=mapped_column(JSON,default=dict); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
class Attempt(Base):
    __tablename__="attempts"; __table_args__=(UniqueConstraint("user_id","idempotency_key"),{"schema":SCHEMA})
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4())); user_id: Mapped[int]=mapped_column(Integer,index=True); assessment_id: Mapped[int]=mapped_column(Integer,index=True)
    engine: Mapped[str]=mapped_column(String(40)); score_percent: Mapped[float]=mapped_column(Float); passed: Mapped[bool]=mapped_column(Boolean); answers: Mapped[dict]=mapped_column(JSON); result: Mapped[dict]=mapped_column(JSON); idempotency_key: Mapped[str|None]=mapped_column(String(200),nullable=True); submitted_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class OutboxEvent(Base):
    __tablename__="outbox"; __table_args__={"schema":SCHEMA}
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4())); topic: Mapped[str]=mapped_column(String(120),index=True); payload: Mapped[dict]=mapped_column(JSON); occurred_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc)); published_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class GeneratedQuiz(Base):
    __tablename__="generated_quizzes"; __table_args__={"schema":SCHEMA}
    id:Mapped[int]=mapped_column(Integer,primary_key=True);user_id:Mapped[int]=mapped_column(Integer,index=True);title:Mapped[str]=mapped_column(String(255));source_name:Mapped[str]=mapped_column(String(255));source_type:Mapped[str]=mapped_column(String(20));source_excerpt:Mapped[str|None]=mapped_column(Text);difficulty:Mapped[str|None]=mapped_column(String(20));generator:Mapped[str|None]=mapped_column(String(20));created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc));questions:Mapped[list["GeneratedQuizQuestion"]]=relationship(cascade="all, delete-orphan",order_by="GeneratedQuizQuestion.order");attempts:Mapped[list["QuizAttempt"]]=relationship(cascade="all, delete-orphan")
class GeneratedQuizQuestion(Base):
    __tablename__="generated_quiz_questions"; __table_args__={"schema":SCHEMA}
    id:Mapped[int]=mapped_column(Integer,primary_key=True);quiz_id:Mapped[int]=mapped_column(ForeignKey(f"{SCHEMA}.generated_quizzes.id",ondelete="CASCADE"),index=True);order:Mapped[int]=mapped_column(Integer,default=0);question_text:Mapped[str]=mapped_column(Text);options:Mapped[list]=mapped_column(JSON);correct_option_index:Mapped[int]=mapped_column(Integer);explanation:Mapped[str|None]=mapped_column(Text);concept:Mapped[str|None]=mapped_column(String(255))
class QuizAttempt(Base):
    __tablename__="quiz_attempts"; __table_args__={"schema":SCHEMA}
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True);quiz_id:Mapped[int]=mapped_column(ForeignKey(f"{SCHEMA}.generated_quizzes.id",ondelete="CASCADE"),index=True);user_id:Mapped[int]=mapped_column(Integer,index=True);answers:Mapped[dict]=mapped_column(JSON);correct_count:Mapped[int]=mapped_column(Integer);total_questions:Mapped[int]=mapped_column(Integer);score_percent:Mapped[float]=mapped_column(Float);submitted_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class StatEngineQuestion(Base):
    __tablename__="stat_engine_questions"; __table_args__={"schema":SCHEMA}
    question_id:Mapped[str]=mapped_column(String(100),primary_key=True);template_id:Mapped[str]=mapped_column(String(100));skill_id:Mapped[str]=mapped_column(String(100),index=True);competency_id:Mapped[str]=mapped_column(String(100));question_type:Mapped[str]=mapped_column(String(50));difficulty:Mapped[str]=mapped_column(String(50));prompt:Mapped[str]=mapped_column(Text);parameters:Mapped[dict]=mapped_column(JSON);correct_answer:Mapped[Any]=mapped_column(JSON);tolerance:Mapped[float|None]=mapped_column(Float);options_map:Mapped[dict]=mapped_column(JSON);correct_option_id:Mapped[str|None]=mapped_column(String(50));explanation:Mapped[str|None]=mapped_column(Text);unit:Mapped[str|None]=mapped_column(String(100));chart:Mapped[dict|None]=mapped_column(JSON);seed:Mapped[int|None]=mapped_column(Integer);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class StatEngineAttempt(Base):
    __tablename__="stat_engine_attempts"; __table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4()));user_id:Mapped[int]=mapped_column(Integer,index=True);question_id:Mapped[str]=mapped_column(String(100),index=True);skill_id:Mapped[str]=mapped_column(String(100));submitted_answer:Mapped[str]=mapped_column(String(255));correct:Mapped[bool]=mapped_column(Boolean);misconception_id:Mapped[str|None]=mapped_column(String(100));time_taken_seconds:Mapped[int|None]=mapped_column(Integer);submitted_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class StatEngineMastery(Base):
    __tablename__="stat_engine_mastery"; __table_args__=(UniqueConstraint("user_id","skill_id"),{"schema":SCHEMA})
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4()));user_id:Mapped[int]=mapped_column(Integer,index=True);skill_id:Mapped[str]=mapped_column(String(100));score:Mapped[float]=mapped_column(Float,default=0);attempts_count:Mapped[int]=mapped_column(Integer,default=0);correct_count:Mapped[int]=mapped_column(Integer,default=0);consecutive_errors:Mapped[int]=mapped_column(Integer,default=0);updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
class GeneratedBehaviouralCase(Base):
    __tablename__="generated_behavioural_cases"; __table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(100),primary_key=True);user_id:Mapped[int]=mapped_column(Integer,index=True);course_id:Mapped[int|None]=mapped_column(Integer,nullable=True,index=True);definition:Mapped[dict]=mapped_column(JSON);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class TechnicalLabTemplate(Base):
    __tablename__="technical_lab_templates"; __table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(100),primary_key=True);title:Mapped[str]=mapped_column(String(255));skill:Mapped[str]=mapped_column(String(255),index=True);language:Mapped[str|None]=mapped_column(String(50));difficulty:Mapped[str|None]=mapped_column(String(50));lab_type:Mapped[str|None]=mapped_column(String(100));tags:Mapped[list]=mapped_column(JSON,default=list);instructions_template:Mapped[str]=mapped_column(Text);starter_code_template:Mapped[str]=mapped_column(Text);solution_template:Mapped[str|None]=mapped_column(Text);constraints:Mapped[list]=mapped_column(JSON,default=list);test_cases_template:Mapped[list]=mapped_column(JSON,default=list);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class CyberSandboxTemplate(Base):
    __tablename__="cyber_sandbox_templates"; __table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(100),primary_key=True);title:Mapped[str]=mapped_column(String(255));category:Mapped[str]=mapped_column(String(100));difficulty:Mapped[str|None]=mapped_column(String(50));competency_id:Mapped[str|None]=mapped_column(String(100));points:Mapped[int|None]=mapped_column(Integer);duration_minutes:Mapped[int|None]=mapped_column(Integer);tags:Mapped[list]=mapped_column(JSON,default=list);mitre_techniques:Mapped[list]=mapped_column(JSON,default=list);scenario_template:Mapped[str]=mapped_column(Text);instructions_template:Mapped[str]=mapped_column(Text);hints_template:Mapped[list]=mapped_column(JSON,default=list);artifacts_spec:Mapped[dict]=mapped_column(JSON,default=dict);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class CyberSandboxChallenge(Base):
    __tablename__="cyber_sandbox_challenges"; __table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(100),primary_key=True);template_id:Mapped[str|None]=mapped_column(String(100));title:Mapped[str]=mapped_column(String(255));category:Mapped[str]=mapped_column(String(100));difficulty:Mapped[str|None]=mapped_column(String(50));points:Mapped[int|None]=mapped_column(Integer);duration_minutes:Mapped[int|None]=mapped_column(Integer);competency_id:Mapped[str|None]=mapped_column(String(100));is_flagship:Mapped[bool]=mapped_column(Boolean,default=False);tags:Mapped[list]=mapped_column(JSON,default=list);mitre_techniques:Mapped[list]=mapped_column(JSON,default=list);objectives:Mapped[list]=mapped_column(JSON,default=list);scenario_markdown:Mapped[str]=mapped_column(Text);flag:Mapped[str]=mapped_column(String(255));hints:Mapped[list]=mapped_column(JSON,default=list);artifacts:Mapped[dict]=mapped_column(JSON,default=dict);notebook_code:Mapped[str]=mapped_column(Text);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

def build_engine(url: str|None=None):
    url=url or get_settings().database_url; kwargs={"connect_args":{"check_same_thread":False}} if url.startswith("sqlite") else {"pool_pre_ping":True}; eng=create_engine(url,**kwargs)
    return eng.execution_options(schema_translate_map={SCHEMA:None}) if url.startswith("sqlite") else eng
engine=build_engine(); SessionLocal=sessionmaker(engine,expire_on_commit=False)
def get_db():
    with SessionLocal() as db: yield db
def initialize_database():
    if not get_settings().auto_create_schema: return
    with engine.begin() as conn:
        if engine.dialect.name=="postgresql": conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
    Base.metadata.create_all(engine)
