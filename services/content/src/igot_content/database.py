from datetime import datetime,timezone
from uuid import uuid4
from sqlalchemy import DateTime,Integer,JSON,String,Text,create_engine,text
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker
from .config import get_settings
SCHEMA="content"
class Base(DeclarativeBase):pass
class Source(Base):
    __tablename__="sources";__table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4()));owner_id:Mapped[int]=mapped_column(Integer,index=True);kind:Mapped[str]=mapped_column(String(30));uri:Mapped[str]=mapped_column(Text);title:Mapped[str]=mapped_column(String(300),default="");status:Mapped[str]=mapped_column(String(30),default="pending");metadata_json:Mapped[dict]=mapped_column(JSON,default=dict);extracted_text:Mapped[str|None]=mapped_column(Text,nullable=True);artifact_uri:Mapped[str|None]=mapped_column(Text,nullable=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Job(Base):
    __tablename__="jobs";__table_args__={"schema":SCHEMA}
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4()));source_id:Mapped[str]=mapped_column(String(36),index=True);owner_id:Mapped[int]=mapped_column(Integer);kind:Mapped[str]=mapped_column(String(50),default="extract");status:Mapped[str]=mapped_column(String(30),default="queued");progress:Mapped[int]=mapped_column(Integer,default=0);error:Mapped[str|None]=mapped_column(Text,nullable=True);result:Mapped[dict]=mapped_column(JSON,default=dict);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class TechnicalTranscript(Base):
    __tablename__="technical_transcripts";__table_args__={"schema":SCHEMA}
    id:Mapped[int]=mapped_column(Integer,primary_key=True);course_id:Mapped[int|None]=mapped_column(Integer,nullable=True,index=True);title:Mapped[str]=mapped_column(String(255));raw_text:Mapped[str]=mapped_column(Text);cleaned_text:Mapped[str]=mapped_column(Text);chunks_json:Mapped[list]=mapped_column(JSON,default=list);metadata_json:Mapped[dict]=mapped_column(JSON,default=dict);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
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
