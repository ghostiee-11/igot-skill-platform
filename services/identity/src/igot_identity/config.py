import os
from dataclasses import dataclass


def _boolean(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://localhost/igot")
    database_schema: str = os.getenv("DATABASE_SCHEMA", "identity")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
    cors_origins: tuple[str, ...] = tuple(filter(None, os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")))
    demo_accounts_enabled: bool = _boolean("DEMO_ACCOUNTS_ENABLED")
    demo_learner_email: str = os.getenv("DEMO_LEARNER_EMAIL", "rajesh.kumar@mospi.gov.in").lower()
    demo_learner_password: str = os.getenv("DEMO_LEARNER_PASSWORD", "")
    demo_learner_name: str = os.getenv("DEMO_LEARNER_NAME", "Rajesh Kumar")


settings = Settings()
