from contextlib import asynccontextmanager
from dataclasses import dataclass
from fastapi import Depends,FastAPI,HTTPException
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from jose import JWTError,jwt
from pydantic import BaseModel,Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from .config import get_settings
from .database import Job,Source,TechnicalTranscript,engine,get_db,initialize_database
from .extraction import chunk_text,clean_transcript,discovery_links
@dataclass
class Principal:user_id:int;role:str
bearer=HTTPBearer(auto_error=False)
def principal(credentials:HTTPAuthorizationCredentials|None=Depends(bearer)):
    if not credentials:raise HTTPException(401,"Authentication required")
    cfg=get_settings()
    if len(cfg.jwt_secret)<32:raise HTTPException(503,"JWT_SECRET must be configured with at least 32 characters")
    try:
        p=jwt.decode(credentials.credentials,cfg.jwt_secret,algorithms=[cfg.jwt_algorithm]);return Principal(int(p["sub"]),str(p.get("role","learner")))
    except (JWTError,KeyError,ValueError,TypeError):raise HTTPException(401,"Invalid authentication token")
@asynccontextmanager
async def lifespan(app):initialize_database();yield
app=FastAPI(title="iGOT Content Service",version="1.0",lifespan=lifespan)
class SourceCreate(BaseModel):kind:str="web";uri:str;title:str="";metadata:dict=Field(default_factory=dict)
class DiscoverRequest(BaseModel):query:str;limit:int=10
class TranscriptRequest(BaseModel):
    title:str=Field(min_length=1,max_length=255);raw_text:str=Field(min_length=10);course_id:int|None=None;metadata:dict=Field(default_factory=dict)
@app.get("/v1/health")
def health():return {"status":"ok","service":"content"}
@app.get("/v1/ready")
def ready():
    try:
        with engine.connect() as c:c.execute(text("SELECT 1"))
        return {"status":"ready"}
    except Exception as exc:raise HTTPException(503,f"database unavailable: {type(exc).__name__}")
@app.post("/v1/sources",status_code=201)
def create_source(req:SourceCreate,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    if req.kind not in {"web","document","video","catalog"}:raise HTTPException(422,"unsupported source kind")
    obj=Source(owner_id=p.user_id,kind=req.kind,uri=req.uri,title=req.title,metadata_json=req.metadata);db.add(obj);db.commit();return {"id":obj.id,"status":obj.status}
@app.get("/v1/sources/{source_id}")
def get_source(source_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    obj=db.get(Source,source_id)
    if not obj or (obj.owner_id!=p.user_id and p.role!="admin"):raise HTTPException(404,"Source not found")
    return {"id":obj.id,"kind":obj.kind,"uri":obj.uri,"title":obj.title,"status":obj.status,"metadata":obj.metadata_json,"artifact_uri":obj.artifact_uri,"extracted_text":obj.extracted_text}
@app.post("/v1/sources/{source_id}/process",status_code=202)
def process_source(source_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    obj=db.get(Source,source_id)
    if not obj or obj.owner_id!=p.user_id:raise HTTPException(404,"Source not found")
    job=Job(source_id=obj.id,owner_id=p.user_id);obj.status="queued";db.add(job);db.commit()
    from .tasks import process_source_job
    try:
        process_source_job.delay(job.id);dispatched=True
    except Exception:
        dispatched=False
    return {"job_id":job.id,"status":"queued","dispatched":dispatched}
@app.get("/v1/jobs/{job_id}")
def get_job(job_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    job=db.get(Job,job_id)
    if not job or (job.owner_id!=p.user_id and p.role!="admin"):raise HTTPException(404,"Job not found")
    return {"id":job.id,"source_id":job.source_id,"status":job.status,"progress":job.progress,"error":job.error,"result":job.result}
@app.post("/v1/discover")
def discover(req:DiscoverRequest,_:Principal=Depends(principal)):return {"query":req.query,"results":discovery_links(req.query,req.limit)}

@app.post("/v1/technical-courses/process")
def process_transcript(req:TranscriptRequest,_:Principal=Depends(principal),db:Session=Depends(get_db)):
    cleaned=clean_transcript(req.raw_text);chunks=chunk_text(cleaned)
    row=TechnicalTranscript(course_id=req.course_id,title=req.title,raw_text=req.raw_text,cleaned_text=cleaned,chunks_json=chunks,metadata_json=req.metadata);db.add(row);db.commit();db.refresh(row)
    return {"id":row.id,"title":row.title,"course_id":row.course_id,"cleaned_length":len(cleaned),"estimated_tokens":sum(item["token_count"] for item in chunks),"chunk_count":len(chunks),"chunks":chunks,"metadata":row.metadata_json}
