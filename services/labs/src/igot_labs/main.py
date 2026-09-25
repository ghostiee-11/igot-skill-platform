import json
import re
import socket
import time
import asyncio
from functools import lru_cache
from datetime import datetime,timedelta,timezone
from secrets import token_urlsafe
from time import perf_counter
from uuid import uuid4
import httpx
import websockets
from fastapi import Depends,FastAPI,HTTPException,Request,Response,WebSocket
from pydantic import BaseModel,Field
from sqlalchemy import select,text
from sqlalchemy.orm import Session
from .config import get_settings
from .database import AccessGrant,Artifact,LabSession,LegacyCyberSession,engine,get_db
from .runtime import DockerRuntime,RuntimeUnavailable
from .security import Principal,internal,principal
app=FastAPI(title="iGOT Labs Service",version="1.0")
class SessionCreate(BaseModel):lab_id:str;target_images:list[str]=Field(default_factory=list);ttl_minutes:int|None=None;metadata:dict=Field(default_factory=dict)
class ExecuteRequest(BaseModel):argv:list[str]
class CellCode(BaseModel):code:str;context_code:str=""
class GradeTest(BaseModel):name:str;test_code:str;is_hidden:bool=False
class GradeCode(BaseModel):code:str;tests:list[GradeTest]
class NotebookExport(BaseModel):title:str;format:str="ipynb";cells:list[dict]
class CyberStart(BaseModel):challenge_id:str;duration_minutes:int=45
class CyberFlag(BaseModel):session_id:str;challenge_id:str|None=None;flag:str
class CyberHint(BaseModel):session_id:str;challenge_id:str|None=None;hint_id:int

def isolated_python(code:str)->dict:
    if len(code)>16000:raise HTTPException(413,"Code is too large for this lab runtime")
    runtime=DockerRuntime();provisioned=None
    try:
        provisioned=runtime.provision(f"run-{uuid4().hex[:16]}",[])
        return runtime.execute(provisioned.workspace_id,["python","-B","-c",code])
    except (RuntimeUnavailable,ValueError) as exc:raise HTTPException(503,str(exc)) from exc
    finally:
        if provisioned:runtime.terminate(provisioned.workspace_id,provisioned.target_ids,provisioned.network_id)
def owned(db:Session,session_id:str,p:Principal)->LabSession:
    record=db.get(LabSession,session_id)
    if not record or (record.owner_id!=p.user_id and p.role!="admin"):raise HTTPException(404,"Lab session not found")
    return record
def present(record:LabSession):return {"id":record.id,"lab_id":record.lab_id,"status":record.status,"expires_at":record.expires_at,"metadata":record.metadata_json}
def expired(record:LabSession)->bool:
    value=record.expires_at
    if value.tzinfo is None:value=value.replace(tzinfo=timezone.utc)
    return value<=datetime.now(timezone.utc)
def cyber_record(db:Session,session_id:str,p:Principal)->tuple[LabSession,LegacyCyberSession]:
    record=owned(db,session_id,p);private=db.get(LegacyCyberSession,session_id)
    if not private or record.metadata_json.get("kind")!="cyber":raise HTTPException(404,"Incident session not found")
    return record,private
def cyber_response(record:LabSession,private:LegacyCyberSession)->dict:
    meta=record.metadata_json;expiry=record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    unlocked=set(private.unlocked_hints or [])
    return {"session_id":record.id,"challenge_id":record.lab_id,"title":meta["title"],"category":meta["category"],"difficulty":meta["difficulty"],"points":max(0,int(meta["points"])-private.total_penalties),"expires_at":expiry.isoformat(),"remaining_seconds":max(0,int((expiry-datetime.now(timezone.utc)).total_seconds())),"status":record.status,"assigned_port":record.access_port,"marimo_url":f"{get_settings().console_public_base_url}/v1/cyber-console/{meta['console_token']}/","hints":[{"id":item["id"],"penalty":item.get("penalty",15),"unlocked":item["id"] in unlocked,**({"content":item.get("content","")} if item["id"] in unlocked else {})} for item in meta["hints"]],"scenario_md":meta["scenario_md"],"objectives":meta["objectives"],"solved":private.is_solved}
def console_host(db:Session,token:str)->str:
    grant=db.get(AccessGrant,token)
    if not grant:raise HTTPException(404,"Console not found")
    expiry=grant.expires_at if grant.expires_at.tzinfo else grant.expires_at.replace(tzinfo=timezone.utc)
    record=db.get(LabSession,grant.session_id)
    if expiry<=datetime.now(timezone.utc) or not record or record.status!="running" or record.metadata_json.get("kind")!="cyber":raise HTTPException(404,"Console not found")
    ensure_console_network(record.network_id)
    return record.metadata_json["workspace_host"]
@lru_cache(maxsize=256)
def ensure_console_network(network_id:str):DockerRuntime().connect_controller(network_id)

@app.api_route("/v1/cyber-console/{token}/{path:path}",methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"])
async def cyber_console_http(token:str,path:str,request:Request,db:Session=Depends(get_db)):
    host=console_host(db,token);upstream_url=f"http://{host}:2718/v1/cyber-console/{token}/{path}"
    headers={key:value for key,value in request.headers.items() if key.lower() not in {"host","connection","content-length","transfer-encoding"}}
    try:
        async with httpx.AsyncClient(timeout=30,follow_redirects=False) as client:
            upstream=await client.request(request.method,upstream_url,params=request.query_params,headers=headers,content=await request.body())
    except httpx.HTTPError as exc:raise HTTPException(502,"Incident console is unavailable") from exc
    result=Response(content=upstream.content,status_code=upstream.status_code)
    result.raw_headers=[(key,value) for key,value in upstream.headers.raw if key.lower() not in {b"connection",b"transfer-encoding",b"content-length",b"content-encoding"}]
    return result

@app.websocket("/v1/cyber-console/{token}/{path:path}")
async def cyber_console_websocket(token:str,path:str,websocket:WebSocket,db:Session=Depends(get_db)):
    try:host=console_host(db,token)
    except HTTPException:
        await websocket.close(code=4404);return
    query=f"?{websocket.url.query}" if websocket.url.query else ""
    target=f"ws://{host}:2718/v1/cyber-console/{token}/{path}{query}"
    try:
        async with websockets.connect(target,origin=websocket.headers.get("origin"),max_size=8*1024*1024) as upstream:
            await websocket.accept()
            async def to_upstream():
                while True:
                    message=await websocket.receive()
                    if message["type"]=="websocket.disconnect":break
                    if message.get("text") is not None:await upstream.send(message["text"])
                    elif message.get("bytes") is not None:await upstream.send(message["bytes"])
            async def to_browser():
                async for message in upstream:
                    if isinstance(message,str):await websocket.send_text(message)
                    else:await websocket.send_bytes(message)
            tasks=[asyncio.create_task(to_upstream()),asyncio.create_task(to_browser())]
            done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            for task in pending:task.cancel()
    except (OSError,websockets.WebSocketException):
        try:await websocket.close(code=1011)
        except RuntimeError:pass

@app.post("/v1/digital-governance/sandbox/session/start",status_code=201)
async def start_cyber_session(req:CyberStart,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    if not 5<=req.duration_minutes<=120:raise HTTPException(422,"duration_minutes must be between 5 and 120")
    cfg=get_settings()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response=await client.get(f"{cfg.assessment_service_url}/v1/internal/cyber-challenges/{req.challenge_id}",headers={"X-Internal-Secret":cfg.internal_event_secret})
            response.raise_for_status();challenge=response.json()
    except httpx.HTTPStatusError as exc:raise HTTPException(404 if exc.response.status_code==404 else 503,"Challenge unavailable") from exc
    except (httpx.RequestError,ValueError) as exc:raise HTTPException(503,"Challenge catalogue unavailable") from exc
    duration=min(req.duration_minutes,int(challenge.get("duration_minutes") or req.duration_minutes))
    session_id=str(uuid4());expiry=datetime.now(timezone.utc)+timedelta(minutes=duration);console_token=token_urlsafe(32);challenge["console_base"]=f"/v1/cyber-console/{console_token}"
    runtime=DockerRuntime();provisioned=None
    try:
        provisioned=runtime.provision(session_id,[],challenge=challenge)
        for _ in range(40):
            try:
                with socket.create_connection((provisioned.workspace_host,2718),timeout=0.5):break
            except OSError:time.sleep(0.25)
        else:
            diagnostic=runtime.execute(provisioned.workspace_id,["sh","-c","tail -c 1200 /tmp/marimo-launch.log 2>/dev/null || true"])
            raise RuntimeUnavailable(f"Marimo did not start: {diagnostic['stdout'][-800:]}")
    except (RuntimeUnavailable,ValueError,OSError) as exc:
        if provisioned:runtime.terminate(provisioned.workspace_id,provisioned.target_ids,provisioned.network_id)
        raise HTTPException(503,f"Incident workbench could not start: {exc}") from exc
    public={key:challenge.get(key) for key in ("title","category","difficulty","points","objectives","scenario_md","hints","competency_id")};public.update(kind="cyber",console_token=console_token,workspace_host=provisioned.workspace_host)
    record=LabSession(id=session_id,owner_id=p.user_id,lab_id=req.challenge_id,status="running",workspace_container_id=provisioned.workspace_id,target_container_ids=[],network_id=provisioned.network_id,access_port=8107,expires_at=expiry,metadata_json=public)
    private=LegacyCyberSession(id=session_id,user_id=p.user_id,challenge_id=req.challenge_id,status="running",assigned_port=8107,flag=challenge["flag"],unlocked_hints=[],total_penalties=0,final_score=0,is_solved=False,created_at=datetime.now(timezone.utc),expires_at=expiry)
    try:db.add_all([record,private,AccessGrant(token=console_token,session_id=session_id,owner_id=p.user_id,expires_at=expiry)]);db.commit()
    except Exception:
        db.rollback();runtime.terminate(provisioned.workspace_id,[],provisioned.network_id);raise
    return cyber_response(record,private)

@app.get("/v1/digital-governance/sandbox/session/{session_id}")
def get_cyber_session(session_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    return cyber_response(*cyber_record(db,session_id,p))

@app.post("/v1/digital-governance/sandbox/session/{session_id}/stop")
def stop_cyber_session(session_id:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    record,private=cyber_record(db,session_id,p)
    if record.status=="running":DockerRuntime().terminate(record.workspace_container_id,record.target_container_ids,record.network_id)
    record.status="terminated";private.status="terminated";db.commit()
    return {"message":"Sandbox session stopped successfully","session_id":session_id}

@app.post("/v1/digital-governance/sandbox/session/submit-flag")
def submit_cyber_flag(req:CyberFlag,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    record,private=cyber_record(db,req.session_id,p)
    if req.challenge_id and req.challenge_id!=record.lab_id:raise HTTPException(422,"Challenge does not match session")
    if record.status!="running" or expired(record):raise HTTPException(409,"Incident session is not active")
    correct=req.flag.strip().casefold()==private.flag.strip().casefold();points=0
    if correct and not private.is_solved:
        points=max(0,int(record.metadata_json["points"])-private.total_penalties);private.is_solved=True;private.status="solved";private.final_score=points;private.solved_at=datetime.now(timezone.utc);db.commit()
    return {"correct":correct,"message":"Incident flag verified." if correct else "Incorrect flag. Check the evidence and try again.","points_awarded":points,"competency_id":record.metadata_json.get("competency_id") or "soc_investigation","competency_score":private.final_score}

@app.post("/v1/digital-governance/sandbox/session/unlock-hint")
def unlock_cyber_hint(req:CyberHint,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    record,private=cyber_record(db,req.session_id,p)
    if req.challenge_id and req.challenge_id!=record.lab_id:raise HTTPException(422,"Challenge does not match session")
    if record.status!="running" or expired(record):raise HTTPException(409,"Incident session is not active")
    hint=next((item for item in record.metadata_json["hints"] if item["id"]==req.hint_id),None)
    if not hint:raise HTTPException(404,"Hint not found")
    if req.hint_id not in private.unlocked_hints:
        private.unlocked_hints=[*private.unlocked_hints,req.hint_id];private.total_penalties+=int(hint.get("penalty",15));db.commit()
    return {"hint_id":req.hint_id,"content":hint.get("content",""),"penalty":hint.get("penalty",15),"remaining_points":max(0,int(record.metadata_json["points"])-private.total_penalties)}

@app.get("/v1/digital-governance/sandbox/competencies")
def cyber_competencies(p:Principal=Depends(principal),db:Session=Depends(get_db)):
    scores={key:0 for key in ("soc_investigation","phishing_analysis","cloud_security","dpi_security","digital_forensics")}
    solved=db.scalars(select(LegacyCyberSession).where(LegacyCyberSession.user_id==p.user_id,LegacyCyberSession.is_solved==True)).all()
    for result in solved:
        record=db.get(LabSession,result.id)
        if not record:continue
        competency=record.metadata_json.get("competency_id") or "soc_investigation"
        if competency not in scores:competency="digital_forensics" if "forensic" in competency or "linux" in competency else "soc_investigation"
        scores[competency]+=result.final_score
    return {**scores,"total_score":sum(scores.values()),"solved_challenges_count":len(solved)}
@app.get("/v1/health")
def health():return {"status":"ok","service":"labs"}
@app.get("/v1/ready")
def ready():
    try:
        with engine.connect() as c:c.execute(text("SELECT 1"))
        DockerRuntime().health();return {"status":"ready"}
    except Exception as exc:raise HTTPException(503,f"lab runtime unavailable: {type(exc).__name__}")

@app.post("/v1/technical-courses/sandbox/execute-code")
def execute_notebook_cell(req:CellCode,_:Principal=Depends(principal)):
    started=perf_counter();result=isolated_python(f"{req.context_code}\n{req.code}")
    return {"success":result["exit_code"]==0,"output":result["stdout"] if result["exit_code"]==0 else result["stderr"],"stdout":result["stdout"],"stderr":result["stderr"],"execution_time_ms":round((perf_counter()-started)*1000),"exit_code":result["exit_code"]}

@app.post("/v1/code/grade",dependencies=[Depends(internal)])
def grade_code(req:GradeCode,_:Principal=Depends(principal)):
    if not req.tests or len(req.tests)>12:raise HTTPException(422,"A lab must have between 1 and 12 tests")
    started=perf_counter();results=[];last_stdout="";last_stderr="";exit_code=0
    for test in req.tests:
        run_started=perf_counter();execution=isolated_python(f"{req.code}\n\n{test.test_code}")
        passed=execution["exit_code"]==0;exit_code=max(exit_code,execution["exit_code"]);last_stdout=execution["stdout"];last_stderr=execution["stderr"]
        results.append({"name":test.name,"passed":passed,"error":None if passed else ("A private check did not pass." if test.is_hidden else execution["stderr"][-1000:] or "The test assertion failed."),"duration_ms":round((perf_counter()-run_started)*1000)})
    passed_count=sum(item["passed"] for item in results)
    return {"all_passed":passed_count==len(results),"passed_tests_count":passed_count,"total_tests_count":len(results),"test_results":results,"execution_time_ms":round((perf_counter()-started)*1000),"stdout":last_stdout,"stderr":last_stderr if results and not results[-1]["passed"] and not req.tests[-1].is_hidden else None,"exit_code":exit_code}

@app.post("/v1/technical-courses/notebook/export")
def export_notebook(req:NotebookExport,_:Principal=Depends(principal)):
    if req.format.lower()!="ipynb":raise HTTPException(422,"Only ipynb export is supported")
    if len(req.cells)>50:raise HTTPException(413,"Notebook has too many cells")
    cells=[]
    for item in req.cells:
        kind="markdown" if item.get("type")=="markdown" else "code"
        content=str(item.get("content") or "")[:20000]
        cell={"cell_type":kind,"metadata":{},"source":content.splitlines(keepends=True)}
        if kind=="code":cell.update(execution_count=None,outputs=[])
        cells.append(cell)
    notebook={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},"nbformat":4,"nbformat_minor":5}
    filename=re.sub(r"[^a-z0-9_-]+","_",req.title.lower()).strip("_")[:80] or "lab"
    return {"filename":f"{filename}.ipynb","content":json.dumps(notebook,ensure_ascii=False,indent=2),"mime_type":"application/x-ipynb+json"}
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
