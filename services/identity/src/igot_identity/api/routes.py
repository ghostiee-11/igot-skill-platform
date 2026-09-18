from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from igot_identity.adapters.database import get_db
from igot_identity.application.security import create_token, current_user, hash_password, verify_password
from igot_identity.config import settings
from igot_identity.domain.models import Department, User, UserProfile

router = APIRouter(prefix="/v1")


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(StrictRequest):
    email: EmailStr
    password: str


class RegisterRequest(LoginRequest):
    full_name: str = Field(min_length=1, max_length=255)
    # Kept for compatibility with the existing frontend payload while making
    # privilege escalation impossible through public registration.
    role: Literal["learner"] = "learner"


class EmailRequest(StrictRequest):
    email: EmailStr


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    bio: str | None = None
    education: str | None = None
    work_experience_years: int | None = Field(None, ge=0)
    prior_training: str | None = None
    designation: str | None = None
    department: str | None = None
    job_role: str | None = None
    current_assignment: str | None = None
    areas_of_interest: list[str] | None = None
    language_pref: Literal["en", "hi"] | None = None
    appearance_pref: Literal["light", "dark"] | None = None
    daily_goal_minutes: int | None = Field(None, ge=1, le=1440)


class OnboardingRequest(ProfileUpdate):
    education: str
    work_experience_years: int = Field(0, ge=0)
    designation: str
    department: str
    job_role: str
    areas_of_interest: list[str] = Field(default_factory=list)


def _auth_response(user: User) -> dict:
    return {"access_token": create_token(user), "token_type": "bearer", "user_id": user.id, "email": user.email,
            "full_name": user.full_name, "role": user.role,
            "onboarding_completed": bool(user.profile and user.profile.onboarding_completed)}


def _profile_response(user: User) -> dict:
    p = user.profile
    return {"user_id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role, "profile": {
        "phone": p.phone or "", "bio": p.bio or "", "education": p.education or "",
        "work_experience_years": p.work_experience_years or 0, "prior_training": p.prior_training or "",
        "designation": p.designation or "", "department": p.department or "", "job_role": p.job_role or "",
        "current_assignment": p.current_assignment or "", "areas_of_interest": p.areas_of_interest.split(",") if p.areas_of_interest else [],
        "language_pref": p.language_pref, "appearance_pref": p.appearance_pref, "daily_goal_minutes": p.daily_goal_minutes,
        "current_streak_days": p.current_streak_days, "onboarding_completed": p.onboarding_completed}}


def _demo_learner(req: LoginRequest, db: Session) -> User | None:
    """Provision/repair the local learner only for the exact configured credentials."""
    if not settings.demo_accounts_enabled or not settings.demo_learner_password:
        return None
    email = req.email.lower()
    if email != settings.demo_learner_email or req.password != settings.demo_learner_password:
        return None
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(req.password),
            full_name=settings.demo_learner_name,
            role="learner",
            is_active=True,
        )
        user.profile = UserProfile(onboarding_completed=True)
        db.add(user)
    else:
        if not verify_password(req.password, user.password_hash):
            user.password_hash = hash_password(req.password)
        user.role = "learner"
        user.is_active = True
        if user.profile is None:
            user.profile = UserProfile(onboarding_completed=True)
        else:
            user.profile.onboarding_completed = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(400, "An account with this official email already exists")
    user = User(email=email, password_hash=hash_password(req.password), full_name=req.full_name.strip(), role="learner")
    user.profile = UserProfile()
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_response(user)


@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = _demo_learner(req, db) or db.scalar(select(User).where(User.email == req.email.lower()))
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Incorrect official email or password")
    if not user.is_active:
        raise HTTPException(403, "This account is inactive")
    return _auth_response(user)


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return _auth_response(user)


@router.post("/auth/forgot-password")
def forgot_password(req: EmailRequest):
    raise HTTPException(
        503,
        "Password recovery delivery is not configured. Contact your platform administrator.",
    )


@router.get("/profiles/me")
@router.get("/profile/")
def get_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not user.profile:
        user.profile = UserProfile()
        db.commit()
    return _profile_response(user)


def _apply_profile(req: ProfileUpdate, user: User) -> None:
    data = req.model_dump(exclude_unset=True)
    if "full_name" in data:
        user.full_name = data.pop("full_name")
    if "areas_of_interest" in data:
        data["areas_of_interest"] = ",".join(data["areas_of_interest"])
    for name, value in data.items():
        setattr(user.profile, name, value)


@router.put("/profiles/me")
@router.put("/profile/")
def update_profile(req: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not user.profile:
        user.profile = UserProfile()
    _apply_profile(req, user)
    db.commit()
    return {"success": True, "message": "Official profile updated successfully."}


@router.get("/onboarding/status")
def onboarding_status(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not user.profile:
        user.profile = UserProfile()
        db.commit()
    return _profile_response(user)


@router.post("/onboarding/complete")
@router.post("/onboarding/save")
def complete_onboarding(req: OnboardingRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not user.profile:
        user.profile = UserProfile()
    _apply_profile(req, user)
    user.profile.onboarding_completed = True
    db.commit()
    return {"success": True, "message": "Onboarding profile saved successfully. Routing to dashboard.", "onboarding_completed": True}


@router.get("/departments")
def departments(db: Session = Depends(get_db)):
    return [{"id": d.id, "name": d.name, "description": d.description} for d in db.scalars(select(Department).order_by(Department.name))]
