from dataclasses import dataclass
from fastapi import Depends,Header,HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from igot_competency.config import settings
@dataclass(frozen=True)
class Principal:user_id:int;role:str
oauth2=OAuth2PasswordBearer(tokenUrl="/v1/auth/login",auto_error=False)
def principal(token:str|None=Depends(oauth2)):
    if not token or len(settings.jwt_secret)<32: raise HTTPException(401,"Authentication credentials were not provided or have expired")
    try:
        p=jwt.decode(token,settings.jwt_secret,algorithms=[settings.jwt_algorithm]); return Principal(int(p["sub"]),p.get("role","learner"))
    except (JWTError,KeyError,ValueError): raise HTTPException(401,"Authentication credentials were not provided or have expired")
def admin(p:Principal=Depends(principal)) -> Principal:
    if p.role != "admin":
        raise HTTPException(403,"Administrator access required for this action")
    return p
def internal(x_internal_secret:str|None=Header(None)):
    if not settings.internal_event_secret or x_internal_secret!=settings.internal_event_secret: raise HTTPException(401,"Invalid internal service credential")
