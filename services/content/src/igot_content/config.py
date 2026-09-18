from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    model_config=SettingsConfigDict(extra="ignore")
    database_url:str="postgresql+psycopg://content_service:content_service@localhost:5432/igot";jwt_secret:str="";jwt_algorithm:str="HS256";rabbitmq_url:str="amqp://guest:guest@localhost:5672//"
    storage_backend:str="local";artifact_storage_root:str="./content-data";supabase_url:str="";supabase_service_key:str="";supabase_bucket:str="content";auto_create_schema:bool=False
@lru_cache
def get_settings():return Settings()
