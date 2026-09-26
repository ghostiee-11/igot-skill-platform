from dataclasses import dataclass
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from .config import get_settings

bearer = HTTPBearer(auto_error=False)
@dataclass(frozen=True)
class Principal:
    user_id: int
    role: str = "learner"
    full_name: str = ""

def current_principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
    if credentials is None: raise HTTPException(401, "Authentication credentials were not provided or have expired")
    cfg=get_settings()
    if len(cfg.jwt_secret) < 32:
        raise HTTPException(503, "JWT_SECRET must be configured with at least 32 characters")
    try:
        payload=jwt.decode(credentials.credentials,cfg.jwt_secret,algorithms=[cfg.jwt_algorithm]); subject=payload.get("sub")
        if subject is None: raise ValueError("missing sub")
        return Principal(int(subject),str(payload.get("role","learner")),str(payload.get("name","")))
    except (JWTError,ValueError,TypeError): raise HTTPException(401,"Authentication credentials were not provided or have expired")

def require_admin(principal: Principal = Depends(current_principal)) -> Principal:
    if principal.role != "admin": raise HTTPException(403,"Administrator access required for this action")
    return principal
