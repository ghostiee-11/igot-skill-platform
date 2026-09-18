from datetime import datetime,timezone
from sqlalchemy import DateTime,Float,ForeignKey,Integer,JSON,String,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column,relationship
from igot_competency.adapters.database import Base,SCHEMA
def now(): return datetime.now(timezone.utc)
P=f"{SCHEMA}." if SCHEMA else ""; T={"schema":SCHEMA} if SCHEMA else {}
class Domain(Base):
    __tablename__="competency_domains"; __table_args__=T
    id:Mapped[int]=mapped_column(Integer,primary_key=True); code:Mapped[str]=mapped_column(String(50),unique=True); name:Mapped[str]=mapped_column(String(255)); description:Mapped[str|None]=mapped_column(Text)
    competencies:Mapped[list["Competency"]]=relationship(back_populates="domain",cascade="all, delete-orphan")
class Competency(Base):
    __tablename__="competencies"; __table_args__=T
    id:Mapped[int]=mapped_column(Integer,primary_key=True); domain_id:Mapped[int]=mapped_column(ForeignKey(P+"competency_domains.id",ondelete="CASCADE")); code:Mapped[str]=mapped_column(String(100),unique=True); name:Mapped[str]=mapped_column(String(255)); description:Mapped[str|None]=mapped_column(Text); max_level:Mapped[int]=mapped_column(Integer,default=5)
    domain:Mapped[Domain]=relationship(back_populates="competencies")
class Evidence(Base):
    __tablename__="evidence"; __table_args__=(UniqueConstraint("event_id","competency_id"),T) if SCHEMA else (UniqueConstraint("event_id","competency_id"),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True); event_id:Mapped[str]=mapped_column(String(100)); user_id:Mapped[int]=mapped_column(Integer,index=True); competency_id:Mapped[int]=mapped_column(ForeignKey(P+"competencies.id")); level:Mapped[float]=mapped_column(Float); source_type:Mapped[str]=mapped_column(String(50)); source_id:Mapped[str]=mapped_column(String(255)); observed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True)); metadata_json:Mapped[dict]=mapped_column(JSON,default=dict); competency:Mapped[Competency]=relationship()
class UserScore(Base):
    __tablename__="user_competency_scores"; __table_args__=(UniqueConstraint("user_id","competency_id"),T) if SCHEMA else (UniqueConstraint("user_id","competency_id"),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(Integer,index=True); competency_id:Mapped[int]=mapped_column(ForeignKey(P+"competencies.id")); level:Mapped[float]=mapped_column(Float,default=0); evidence_source:Mapped[str]=mapped_column(String(50)); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now); competency:Mapped[Competency]=relationship()
class Profile(Base):
    __tablename__="competency_profiles"; __table_args__=T
    id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(Integer,unique=True,index=True); statistical_score:Mapped[float]=mapped_column(Float,default=0); technical_score:Mapped[float]=mapped_column(Float,default=0); digital_governance_score:Mapped[float]=mapped_column(Float,default=0); behavioural_score:Mapped[float]=mapped_column(Float,default=0); last_computed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class Gap(Base):
    __tablename__="gap_analyses"; __table_args__=T
    id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(Integer,index=True); domain_id:Mapped[int]=mapped_column(ForeignKey(P+"competency_domains.id")); target_level:Mapped[float]=mapped_column(Float); current_level:Mapped[float]=mapped_column(Float); gap:Mapped[float]=mapped_column(Float); generated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); domain:Mapped[Domain]=relationship()
class Skill(Base):
    __tablename__="skills"; __table_args__=T
    id:Mapped[int]=mapped_column(Integer,primary_key=True); name:Mapped[str]=mapped_column(String(255),unique=True); category:Mapped[str]=mapped_column(String(100),default="Technical")
class UserSkill(Base):
    __tablename__="user_skills"; __table_args__=T
    id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(Integer,index=True); skill_id:Mapped[int]=mapped_column(ForeignKey(P+"skills.id")); source_course_id:Mapped[int|None]=mapped_column(Integer); competency_id:Mapped[int|None]=mapped_column(ForeignKey(P+"competencies.id")); acquired_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); skill:Mapped[Skill]=relationship()
class EvidenceMapping(Base):
    __tablename__="evidence_competency_mapping"; __table_args__=(UniqueConstraint("source_system","source_key"),T) if SCHEMA else (UniqueConstraint("source_system","source_key"),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True); source_system:Mapped[str]=mapped_column(String(50)); source_key:Mapped[str]=mapped_column(String(255)); competency_id:Mapped[int]=mapped_column(ForeignKey(P+"competencies.id",ondelete="CASCADE")); competency:Mapped[Competency]=relationship()
class Recommendation(Base):
    __tablename__="recommendations"; __table_args__=T
    id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(Integer,index=True); course_id:Mapped[int|None]=mapped_column(Integer); course_title:Mapped[str|None]=mapped_column(String(255)); reason:Mapped[str]=mapped_column(Text); score:Mapped[float]=mapped_column(Float,default=0); status:Mapped[str]=mapped_column(String(20),default="pending"); generated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class CourseCandidate(Base):
    __tablename__="course_candidates"; __table_args__=T
    course_id:Mapped[int]=mapped_column(Integer,primary_key=True); title:Mapped[str]=mapped_column(String(255)); category:Mapped[str]=mapped_column(String(100)); difficulty:Mapped[str]=mapped_column(String(50)); overview:Mapped[str]=mapped_column(Text); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class UserCyberCompetency(Base):
    __tablename__="user_cyber_competencies"; __table_args__=T
    id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(Integer,unique=True); soc_investigation:Mapped[int]=mapped_column(Integer,default=0); phishing_analysis:Mapped[int]=mapped_column(Integer,default=0); cloud_security:Mapped[int]=mapped_column(Integer,default=0); dpi_security:Mapped[int]=mapped_column(Integer,default=0); digital_forensics:Mapped[int]=mapped_column(Integer,default=0); total_score:Mapped[int]=mapped_column(Integer,default=0); solved_challenges_count:Mapped[int]=mapped_column(Integer,default=0); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
