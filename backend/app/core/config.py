import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Automatically load environment variables from root and backend .env
root_dir = Path(__file__).resolve().parents[3]
backend_dir = Path(__file__).resolve().parents[2]
if (root_dir / ".env").exists():
    load_dotenv(dotenv_path=root_dir / ".env", override=False)
if (backend_dir / ".env").exists():
    load_dotenv(dotenv_path=backend_dir / ".env", override=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "iGot Karmayogi - AI Skill Intelligence Platform"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "karmayogi-secret-jwt-key-2026-phase-0")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # SQLite default database, can be swapped with postgresql+psycopg2://...
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./karmayogi.db")
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # LLM keys for LangChain / LangGraph AI Assistant & Content Generation
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    NIM_API_KEY: str = os.getenv("NIM_API_KEY", "")
    NIM_MODEL: str = os.getenv("NIM_MODEL", "meta/llama-3.1-8b-instruct")

    # Pinecone vector DB for the recommendation engine's semantic search
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "igot-competency-recommendations")

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    class Config:
        case_sensitive = True

settings = Settings()
