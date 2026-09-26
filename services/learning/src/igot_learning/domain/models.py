from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from igot_learning.adapters.database import Base, SCHEMA

def now(): return datetime.now(timezone.utc)
P = f"{SCHEMA}." if SCHEMA else ""
T = {"schema": SCHEMA} if SCHEMA else {}

class Course(Base):
    __tablename__="courses"; __table_args__=T
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    title: Mapped[str]=mapped_column(String(255),index=True); overview: Mapped[str]=mapped_column(Text)
    instructor: Mapped[str]=mapped_column(String(255)); organization: Mapped[str]=mapped_column(String(255))
    duration_hours: Mapped[float]=mapped_column(Float,default=4); difficulty: Mapped[str]=mapped_column(String(50),default="intermediate")
    source: Mapped[str]=mapped_column(String(50),default="internal"); category: Mapped[str]=mapped_column(String(100),default="General",index=True)
    thumbnail_url: Mapped[str|None]=mapped_column(String(500)); rating: Mapped[float]=mapped_column(Float,default=4.8)
    enrolled_count: Mapped[int]=mapped_column(Integer,default=0); is_popular: Mapped[bool]=mapped_column(Boolean,default=False)
    is_new: Mapped[bool]=mapped_column(Boolean,default=False); assessment_id: Mapped[int|None]=mapped_column(Integer)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    modules: Mapped[list["Module"]]=relationship(back_populates="course",cascade="all, delete-orphan",order_by="Module.position")
    course_skills: Mapped[list["CourseSkill"]]=relationship(back_populates="course",cascade="all, delete-orphan")

class Module(Base):
    __tablename__="modules"; __table_args__=T
    id: Mapped[int]=mapped_column(Integer,primary_key=True); course_id: Mapped[int]=mapped_column(ForeignKey(P+"courses.id",ondelete="CASCADE"),index=True)
    title: Mapped[str]=mapped_column(String(255)); description: Mapped[str|None]=mapped_column(Text); position: Mapped[int]=mapped_column("order",Integer,default=1)
    course: Mapped[Course]=relationship(back_populates="modules"); lessons: Mapped[list["Lesson"]]=relationship(back_populates="module",cascade="all, delete-orphan",order_by="Lesson.position")

class Lesson(Base):
    __tablename__="lessons"; __table_args__=T
    id: Mapped[int]=mapped_column(Integer,primary_key=True); module_id: Mapped[int]=mapped_column(ForeignKey(P+"modules.id",ondelete="CASCADE"),index=True)
    title: Mapped[str]=mapped_column(String(255)); content_type: Mapped[str]=mapped_column(String(50),default="reading")
    duration_minutes: Mapped[int]=mapped_column(Integer,default=15); content: Mapped[str]=mapped_column(Text); video_url: Mapped[str|None]=mapped_column(String(500))
    activity_question: Mapped[str|None]=mapped_column(Text); activity_options_json: Mapped[str|None]=mapped_column(Text)
    activity_correct_option: Mapped[int|None]=mapped_column(Integer); activity_explanation: Mapped[str|None]=mapped_column(Text)
    position: Mapped[int]=mapped_column("order",Integer,default=1); module: Mapped[Module]=relationship(back_populates="lessons")

class Skill(Base):
    __tablename__="skills"; __table_args__=T
    id: Mapped[int]=mapped_column(Integer,primary_key=True); name: Mapped[str]=mapped_column(String(255),unique=True); category: Mapped[str]=mapped_column(String(100),default="Technical")
class CourseSkill(Base):
    __tablename__="course_skills"; __table_args__=(UniqueConstraint("course_id","skill_id"),T) if SCHEMA else (UniqueConstraint("course_id","skill_id"),)
    id: Mapped[int]=mapped_column(Integer,primary_key=True); course_id: Mapped[int]=mapped_column(ForeignKey(P+"courses.id",ondelete="CASCADE")); skill_id: Mapped[int]=mapped_column(ForeignKey(P+"skills.id",ondelete="CASCADE"))
    course: Mapped[Course]=relationship(back_populates="course_skills"); skill: Mapped[Skill]=relationship()
class Enrollment(Base):
    __tablename__="enrollments"; __table_args__=(UniqueConstraint("user_id","course_id"),T) if SCHEMA else (UniqueConstraint("user_id","course_id"),)
    id: Mapped[int]=mapped_column(Integer,primary_key=True); user_id: Mapped[int]=mapped_column(Integer,index=True); course_id: Mapped[int]=mapped_column(ForeignKey(P+"courses.id",ondelete="CASCADE"),index=True)
    status: Mapped[str]=mapped_column(String(50),default="in_progress"); started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    completed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); progress_percent: Mapped[float]=mapped_column(Float,default=0); last_lesson_id: Mapped[int|None]=mapped_column(Integer)
    course: Mapped[Course]=relationship(); progress_records: Mapped[list["Progress"]]=relationship(back_populates="enrollment",cascade="all, delete-orphan")
class Progress(Base):
    __tablename__="progress_records"; __table_args__=(UniqueConstraint("enrollment_id","lesson_id"),T) if SCHEMA else (UniqueConstraint("enrollment_id","lesson_id"),)
    id: Mapped[int]=mapped_column(Integer,primary_key=True); enrollment_id: Mapped[int]=mapped_column(ForeignKey(P+"enrollments.id",ondelete="CASCADE")); module_id: Mapped[int]=mapped_column(Integer); lesson_id: Mapped[int]=mapped_column(Integer)
    completed: Mapped[bool]=mapped_column(Boolean,default=True); activity_completed: Mapped[bool]=mapped_column(Boolean,default=False); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
    enrollment: Mapped[Enrollment]=relationship(back_populates="progress_records")
class LearningHistory(Base):
    __tablename__="learning_history"; __table_args__=(UniqueConstraint("user_id","course_id"),T) if SCHEMA else (UniqueConstraint("user_id","course_id"),)
    id: Mapped[int]=mapped_column(Integer,primary_key=True); user_id: Mapped[int]=mapped_column(Integer,index=True); course_id: Mapped[int]=mapped_column(ForeignKey(P+"courses.id",ondelete="CASCADE")); viewed_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
    course: Mapped[Course]=relationship()
class SearchHistory(Base):
    __tablename__="search_history"; __table_args__=T
    id: Mapped[int]=mapped_column(Integer,primary_key=True); user_id: Mapped[int]=mapped_column(Integer,index=True); query: Mapped[str]=mapped_column(String(255)); searched_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class PlannedCourse(Base):
    __tablename__="planned_courses"; __table_args__=T
    id: Mapped[int]=mapped_column(Integer,primary_key=True); user_id: Mapped[int]=mapped_column(Integer,index=True); course_id: Mapped[int]=mapped_column(ForeignKey(P+"courses.id",ondelete="CASCADE")); planned_for: Mapped[str|None]=mapped_column(String(100)); source: Mapped[str]=mapped_column(String(50),default="self"); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    course: Mapped[Course]=relationship()
class Certificate(Base):
    __tablename__="certificates"; __table_args__=(UniqueConstraint("user_id","course_id"),T) if SCHEMA else (UniqueConstraint("user_id","course_id"),)
    id: Mapped[int]=mapped_column(Integer,primary_key=True); user_id: Mapped[int]=mapped_column(Integer,index=True); course_id: Mapped[int]=mapped_column(ForeignKey(P+"courses.id",ondelete="CASCADE")); attempt_id: Mapped[int|None]=mapped_column(Integer); score_percent: Mapped[float]=mapped_column(Float); issued_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); course: Mapped[Course]=relationship()
class ProcessedEvent(Base):
    __tablename__="processed_events"; __table_args__=T
    event_id: Mapped[str]=mapped_column(String(100),primary_key=True); event_type: Mapped[str]=mapped_column(String(100)); processed_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class LearnerProjection(Base):
    """Identity-owned fields required by learning admin/dashboard read models."""
    __tablename__="learner_projections"; __table_args__=T
    user_id: Mapped[int]=mapped_column(Integer,primary_key=True); email: Mapped[str]=mapped_column(String(255)); full_name: Mapped[str]=mapped_column(String(255)); role: Mapped[str]=mapped_column(String(50),default="learner"); designation: Mapped[str|None]=mapped_column(String(255)); department: Mapped[str|None]=mapped_column(String(255)); onboarding_completed: Mapped[bool]=mapped_column(Boolean,default=False); daily_goal_minutes: Mapped[int]=mapped_column(Integer,default=30); current_streak_days: Mapped[int]=mapped_column(Integer,default=1); last_active_date: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class AssessmentProjection(Base):
    """Assessment-owned aggregate data used by the learning admin view."""
    __tablename__="assessment_projections"; __table_args__=T
    assessment_id: Mapped[int]=mapped_column(Integer,primary_key=True); course_id: Mapped[int]=mapped_column(Integer,index=True); title: Mapped[str]=mapped_column(String(255)); attempts: Mapped[int]=mapped_column(Integer,default=0); passed_attempts: Mapped[int]=mapped_column(Integer,default=0); struggling_questions_json: Mapped[str]=mapped_column(Text,default="[]"); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
