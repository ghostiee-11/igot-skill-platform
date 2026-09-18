from dataclasses import dataclass
from fastapi import Depends,HTTPException
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from jose import JWTError,jwt
from .config import get_settings
bearer=HTTPBearer(auto_error=False)
@dataclass(frozen=True)
class Principal:user_id:int;role:str="learner"
def principal(credentials:HTTPAuthorizationCredentials|None=Depends(bearer)):
    cfg=get_settings()
    if not credentials:raise HTTPException(401,"Authentication required")
    if len(cfg.jwt_secret)<32:raise HTTPException(503,"JWT_SECRET must be configured with at least 32 characters")
    try:
        claims=jwt.decode(credentials.credentials,cfg.jwt_secret,algorithms=[cfg.jwt_algorithm]);return Principal(int(claims["sub"]),str(claims.get("role","learner")))
    except (JWTError,KeyError,ValueError,TypeError):raise HTTPException(401,"Invalid authentication token")
