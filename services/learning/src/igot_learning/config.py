import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://localhost/igot")
    database_schema: str = os.getenv("DATABASE_SCHEMA", "learning")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    internal_event_secret: str = os.getenv("INTERNAL_EVENT_SECRET", "")
    cors_origins: tuple[str, ...] = tuple(filter(None, os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")))
settings = Settings()
