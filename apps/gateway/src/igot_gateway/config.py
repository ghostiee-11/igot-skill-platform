from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GATEWAY_", case_sensitive=False)

    identity_url: str = "http://localhost:8101"
    learning_url: str = "http://localhost:8102"
    assessment_url: str = "http://localhost:8103"
    competency_url: str = "http://localhost:8104"
    ai_url: str = "http://localhost:8105"
    content_url: str = "http://localhost:8106"
    labs_url: str = "http://localhost:8107"
    request_timeout_seconds: float = 60.0
    cors_origins: str = "http://localhost:3000"

    @property
    def service_urls(self) -> dict[str, str]:
        return {
            "identity": self.identity_url.rstrip("/"),
            "learning": self.learning_url.rstrip("/"),
            "assessment": self.assessment_url.rstrip("/"),
            "competency": self.competency_url.rstrip("/"),
            "ai": self.ai_url.rstrip("/"),
            "content": self.content_url.rstrip("/"),
            "labs": self.labs_url.rstrip("/"),
        }

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
