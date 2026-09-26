import datetime
import hashlib
import hmac
import os

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from igot_identity.adapters.database import get_db
from igot_identity.config import settings
from igot_identity.domain.models import User

oauth2 = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${key.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt, expected = encoded.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _require_secret() -> str:
    if len(settings.jwt_secret) < 32:
        raise HTTPException(503, "JWT_SECRET must be configured with at least 32 characters")
    return settings.jwt_secret


def create_token(user: User) -> str:
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(user.id), "role": user.role, "name": user.full_name, "exp": expires},
        _require_secret(),
        algorithm=settings.jwt_algorithm,
    )


def current_user(token: str | None = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(401, "Authentication credentials were not provided or have expired", headers={"WWW-Authenticate": "Bearer"})
    try:
        subject = jwt.decode(token, _require_secret(), algorithms=[settings.jwt_algorithm]).get("sub")
        user = db.get(User, int(subject)) if subject is not None else None
    except (JWTError, ValueError, TypeError):
        user = None
    if not user:
        raise HTTPException(401, "Authentication credentials were not provided or have expired", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(403, "This account is inactive")
    return user
