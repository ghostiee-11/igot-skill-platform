from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from igot_identity.adapters.database import Base, SCHEMA


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="learner")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    profile: Mapped["UserProfile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA + '.' if SCHEMA else ''}users.id", ondelete="CASCADE"), unique=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    bio: Mapped[str | None] = mapped_column(Text)
    education: Mapped[str | None] = mapped_column(String(255))
    work_experience_years: Mapped[int] = mapped_column(Integer, default=0)
    prior_training: Mapped[str | None] = mapped_column(Text)
    designation: Mapped[str | None] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255))
    job_role: Mapped[str | None] = mapped_column(String(255))
    current_assignment: Mapped[str | None] = mapped_column(Text)
    areas_of_interest: Mapped[str | None] = mapped_column(Text)
    language_pref: Mapped[str] = mapped_column(String(20), default="en")
    appearance_pref: Mapped[str] = mapped_column(String(20), default="light")
    profile_pic_url: Mapped[str | None] = mapped_column(String(500))
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_goal_minutes: Mapped[int] = mapped_column(Integer, default=30)
    current_streak_days: Mapped[int] = mapped_column(Integer, default=1)
    last_active_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    user: Mapped[User] = relationship(back_populates="profile")


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = {"schema": SCHEMA} if SCHEMA else {}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
