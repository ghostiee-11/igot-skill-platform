from datetime import datetime,timezone
from uuid import uuid4
from sqlalchemy import Boolean,DateTime,Integer,JSON,String,Text,create_engine,text
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker
from .config import get_settings
SCHEMA="labs"
class Base(DeclarativeBase):pass
class LabSession(Base):
    __tablename__="sessions";__table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4()));owner_id:Mapped[int]=mapped_column(Integer,index=True);lab_id:Mapped[str]=mapped_column(String(100),index=True);status:Mapped[str]=mapped_column(String(30),default="provisioning");workspace_container_id:Mapped[str|None]=mapped_column(String(100),nullable=True);target_container_ids:Mapped[list]=mapped_column(JSON,default=list);network_id:Mapped[str|None]=mapped_column(String(100),nullable=True);access_port:Mapped[int|None]=mapped_column(Integer,nullable=True);expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));metadata_json:Mapped[dict]=mapped_column(JSON,default=dict);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc));updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
class AccessGrant(Base):
    __tablename__="access_grants";__table_args__={"schema":SCHEMA}
    token:Mapped[str]=mapped_column(String(64),primary_key=True);session_id:Mapped[str]=mapped_column(String(36),index=True);owner_id:Mapped[int]=mapped_column(Integer);expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));used_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class Artifact(Base):
    __tablename__="artifacts";__table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4()));session_id:Mapped[str]=mapped_column(String(36),index=True);owner_id:Mapped[int]=mapped_column(Integer);name:Mapped[str]=mapped_column(String(200));uri:Mapped[str]=mapped_column(Text);metadata_json:Mapped[dict]=mapped_column(JSON,default=dict)
class LegacyCyberSession(Base):
    __tablename__="legacy_cyber_sessions";__table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(100),primary_key=True);user_id:Mapped[int|None]=mapped_column(Integer,index=True);challenge_id:Mapped[str]=mapped_column(String(100),index=True);status:Mapped[str|None]=mapped_column(String(50));assigned_port:Mapped[int]=mapped_column(Integer);flag:Mapped[str]=mapped_column(String(255));unlocked_hints:Mapped[list]=mapped_column(JSON,default=list);total_penalties:Mapped[int]=mapped_column(Integer,default=0);final_score:Mapped[int]=mapped_column(Integer,default=0);is_solved:Mapped[bool]=mapped_column(Boolean,default=False);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True));solved_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
def build_engine(url=None):
    url=url or get_settings().database_url;eng=create_engine(url,**({"connect_args":{"check_same_thread":False}} if url.startswith("sqlite") else {"pool_pre_ping":True}));return eng.execution_options(schema_translate_map={SCHEMA:None}) if url.startswith("sqlite") else eng
engine=build_engine();SessionLocal=sessionmaker(engine,expire_on_commit=False)
def get_db():
    with SessionLocal() as db:yield db
def initialize_database():
    if not get_settings().auto_create_schema:return
    with engine.begin() as conn:
        if engine.dialect.name=="postgresql":conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
    Base.metadata.create_all(engine)
