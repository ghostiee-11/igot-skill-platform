from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from igot_identity.config import settings


def _normalize(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = _normalize(settings.database_url)
IS_SQLITE = DATABASE_URL.startswith("sqlite")
SCHEMA = None if IS_SQLITE else settings.database_schema


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    pool_pre_ping=not IS_SQLITE,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
