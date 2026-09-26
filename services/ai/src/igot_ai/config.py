from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    model_config=SettingsConfigDict(extra="ignore")
    jwt_secret:str="";jwt_algorithm:str="HS256";provider_order:str="groq,nim,gemini,openai"
    groq_api_key:str="";groq_model:str="openai/gpt-oss-120b";nim_api_key:str="";nim_model:str="meta/llama-3.1-70b-instruct"
    gemini_api_key:str="";gemini_model:str="gemini-2.0-flash";openai_api_key:str="";openai_model:str="gpt-4o-mini"
@lru_cache
def get_settings():return Settings()
