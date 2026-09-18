from datetime import datetime,timedelta,timezone
from secrets import token_urlsafe
from fastapi import Depends,FastAPI,HTTPException,Response
from pydantic import BaseModel,Field
from sqlalchemy import select,text
from sqlalchemy.orm import Session
from .config import get_settings
from .database import AccessGrant,Artifact,LabSession,engine,get_db
from .runtime import DockerRuntime,RuntimeUnavailable
from .security import Principal,principal
app=FastAPI(title="iGOT Labs Service",version="1.0")
class SessionCreate(BaseModel):lab_id:str;target_images:list[str]=Field(default_factory=list);ttl_minutes:int|None=None;metadata:dict=Field(default_factory=dict)
class ExecuteRequest(BaseModel):argv:list[str]
def owned(db:Session,session_id:str,p:Principal)->LabSession:
    record=db.get(LabSession,session_id)
    if not record or (record.owner_id!=p.user_id and p.role!="admin"):raise HTTPException(404,"Lab session not found")
    return record
def present(record:LabSession):return {"id":record.id,"lab_id":record.lab_id,"status":record.status,"expires_at":record.expires_at,"metadata":record.metadata_json}
def expired(record:LabSession)->bool:
    value=record.expires_at
    if value.tzinfo is None:value=value.replace(tzinfo=timezone.utc)
    return value<=datetime.now(timezone.utc)
@app.get("/v1/health")
def health():return {"status":"ok","service":"labs"}
@app.get("/v1/ready")
def ready():
    try:
        with engine.connect() as c:c.execute(text("SELECT 1"))
        DockerRuntime().health();return {"status":"ready"}
    except Exception as exc:raise HTTPException(503,f"lab runtime unavailable: {type(exc).__name__}")
@app.post("/v1/sessions",status_code=201)
def create(req:SessionCreate,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    ttl=req.ttl_minutes or get_settings().default_ttl_minutes
    if ttl<5 or ttl>240:raise HTTPException(422,"ttl_minutes must be between 5 and 240")
    record=LabSession(owner_id=p.user_id,lab_id=req.lab_id,expires_at=datetime.now(timezone.utc)+timedelta(minutes=ttl),metadata_json={**req.metadata,"target_images":req.target_images});db.add(record);db.commit()
    try:
        provisioned=DockerRuntime().provision(record.id,req.target_images);record.workspace_container_id=provisioned.workspace_id;record.target_container_ids=provisioned.target_ids;record.network_id=provisioned.network_id;record.metadata_json={**record.metadata_json,"workspace_host":provisioned.workspace_host};record.status="running";db.commit()
    except (RuntimeUnavailable,ValueError) as exc:record.status="failed";db.commit();raise HTTPException(503,str(exc))
    return present(record)
@app.get("/v1/sessions/{session_id}")
def get_session(session_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):return present(owned(db,session_id,p))
@app.post("/v1/sessions/{session_id}/access",status_code=201)
def access(session_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    record=owned(db,session_id,p)
    if record.status!="running" or expired(record):raise HTTPException(409,"Lab session is not active")
    record_expiry=record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    token=token_urlsafe(32);expires=min(record_expiry,datetime.now(timezone.utc)+timedelta(minutes=10));db.add(AccessGrant(token=token,session_id=record.id,owner_id=p.user_id,expires_at=expires));db.commit()
    return {"access_url":f"{get_settings().public_base_url}/v1/lab-access/{token}/","expires_at":expires}
@app.post("/v1/sessions/{session_id}/execute")
def execute(session_id:str,req:ExecuteRequest,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    record=owned(db,session_id,p)
    if record.status!="running" or expired(record):raise HTTPException(409,"Lab session is not active")
    try:return DockerRuntime().execute(record.workspace_container_id,req.argv)
    except (RuntimeUnavailable,ValueError) as exc:raise HTTPException(422,str(exc))
@app.post("/v1/sessions/{session_id}/reset")
def reset(session_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    record=owned(db,session_id,p);runtime=DockerRuntime();images=record.metadata_json.get("target_images",[])
    runtime.terminate(record.workspace_container_id,record.target_container_ids,record.network_id);new=runtime.provision(record.id,images)
    record.workspace_container_id=new.workspace_id;record.target_container_ids=new.target_ids;record.network_id=new.network_id;record.metadata_json={**record.metadata_json,"workspace_host":new.workspace_host};record.status="running";db.commit();return present(record)
@app.post("/v1/sessions/{session_id}/artifacts",status_code=201)
def collect(session_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    record=owned(db,session_id,p)
    try:data,meta=DockerRuntime().archive(record.workspace_container_id)
    except (RuntimeUnavailable,ValueError) as exc:raise HTTPException(422,str(exc))
    # Durable object-storage adapter is the next deployment concern; do not place bytes in the database.
    artifact=Artifact(session_id=record.id,owner_id=p.user_id,name="workspace.tar",uri=f"runtime://{record.id}/workspace.tar",metadata_json={"size":len(data),"docker":meta});db.add(artifact);db.commit();return {"id":artifact.id,"name":artifact.name,"size":len(data)}
@app.post("/v1/sessions/{session_id}/terminate")
def terminate(session_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    record=owned(db,session_id,p);DockerRuntime().terminate(record.workspace_container_id,record.target_container_ids,record.network_id);record.status="terminated";db.commit();return present(record)
@app.get("/v1/lab-access/{token}/{path:path}")
def authorize_access(token:str,path:str,db:Session=Depends(get_db)):
    grant=db.get(AccessGrant,token)
    if not grant:raise HTTPException(404,"Access grant not found")
    grant_expiry=grant.expires_at if grant.expires_at.tzinfo else grant.expires_at.replace(tzinfo=timezone.utc)
    if grant_expiry<=datetime.now(timezone.utc):raise HTTPException(404,"Access grant not found")
    record=db.get(LabSession,grant.session_id)
    if not record or record.status!="running":raise HTTPException(409,"Lab session is not active")
    # Gateway/ingress consumes the authenticated target. It must proxy HTTP and WebSocket traffic internally.
    grant.used_at=datetime.now(timezone.utc);db.commit();return {"session_id":record.id,"workspace_host":record.metadata_json.get("workspace_host"),"workspace_port":2718,"path":"/"+path}
