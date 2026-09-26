from dataclasses import dataclass
from typing import Literal
from fastapi import Depends,FastAPI,HTTPException
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from jose import JWTError,jwt
from pydantic import BaseModel,Field
from .config import get_settings
from .providers import MultiProvider,ProviderUnavailable,extract_json
app=FastAPI(title="iGOT AI Service",version="1.0");bearer=HTTPBearer(auto_error=False)
@dataclass
class Principal:user_id:int
def optional_principal(credentials:HTTPAuthorizationCredentials|None=Depends(bearer)):
    if not credentials:return None
    cfg=get_settings()
    if len(cfg.jwt_secret)<32:raise HTTPException(503,"JWT_SECRET must be configured with at least 32 characters")
    try:
        payload=jwt.decode(credentials.credentials,cfg.jwt_secret,algorithms=[cfg.jwt_algorithm]);return Principal(int(payload["sub"]))
    except (JWTError,KeyError,ValueError,TypeError):raise HTTPException(401,"Invalid authentication token")
def principal(value:Principal|None=Depends(optional_principal)):
    if value is None:raise HTTPException(401,"Authentication required")
    return value
class ChatMessage(BaseModel):
    role:Literal["system","user","assistant"]
    content:str=Field(min_length=1,max_length=20000)
class CompletionRequest(BaseModel):messages:list[ChatMessage]=Field(min_length=1,max_length=30);preferred_provider:Literal["groq","nim","gemini","openai"]|None=None
class JSONRequest(CompletionRequest):schema_hint:dict=Field(default_factory=dict)
class AgentRequest(BaseModel):
    message:str=Field(min_length=1,max_length=4000)
    context:str|None=Field(default=None,max_length=4000)
@app.get("/v1/health")
def health():return {"status":"ok","service":"ai"}
@app.get("/v1/ready")
def ready():
    cfg=get_settings();configured=[p for p in cfg.provider_order.split(",") if getattr(cfg,f"{p.strip()}_api_key","")];return {"status":"ready" if configured else "degraded","configured_providers":configured}
@app.post("/v1/chat/completions")
async def complete(req:CompletionRequest,_:Principal=Depends(principal)):
    try:return await MultiProvider().complete([m.model_dump() for m in req.messages],req.preferred_provider)
    except ProviderUnavailable as exc:raise HTTPException(503,str(exc))
@app.post("/v1/generate/json")
async def generate_json(req:JSONRequest,_:Principal=Depends(principal)):
    messages=[*[m.model_dump() for m in req.messages],{"role":"system","content":f"Return one JSON object matching this shape: {req.schema_hint}"}]
    try:
        answer=await MultiProvider().complete(messages,req.preferred_provider);return {**answer,"data":extract_json(answer["content"])}
    except ProviderUnavailable as exc:raise HTTPException(503,str(exc))
    except (ValueError,TypeError) as exc:raise HTTPException(502,str(exc))

def _fallback(message:str,context:str)->str:
    query=message.lower()
    if any(term in query for term in ("cpi","inflation","price index")):
        return "CPI measures price change for a representative consumption basket. Use the approved base period, item weights and published price relatives for the series you are analysing."
    if any(term in query for term in ("sample","survey","nss")):
        return "Official surveys require a documented frame, stratification and selection method. Check the survey's current methodology before choosing estimators or interpreting sampling error."
    return f"I can explain course material and help you navigate learning activities. Current context: {context}."

@app.post("/v1/agents/chat")
async def agent_chat(req:AgentRequest,user:Principal|None=Depends(optional_principal)):
    query=req.message.lower()
    if "gap" in query or "competenc" in query:
        return {"response":"Open your competency profile to run the evidence-backed analysis.","source":"assistant-router","intent":"gap_analysis","actions":[{"label":"View competency profile","href":"/competency" if user else "/login"}]}
    if "recommend" in query or "which course" in query:
        return {"response":"Course recommendations are generated from your current competency gaps.","source":"assistant-router","intent":"recommendations","actions":[{"label":"See recommendations","href":"/recommendations" if user else "/login"}]}
    messages=[{"role":"system","content":"You are the iGOT Karmayogi learning assistant. Be concise and factual."},{"role":"user","content":f"Context: {req.context or 'iGOT learning platform'}\nQuestion: {req.message}"}]
    try:
        answer=await MultiProvider().complete(messages)
        return {"response":answer["content"],"source":answer["provider"],"intent":"tutor","actions":[]}
    except ProviderUnavailable:
        return {"response":_fallback(req.message,req.context or "iGOT learning platform"),"source":"deterministic-fallback","intent":"tutor","actions":[]}
