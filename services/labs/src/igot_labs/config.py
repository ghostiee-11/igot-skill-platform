from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    model_config=SettingsConfigDict(extra="ignore")
    database_url:str="postgresql+psycopg://labs_service:labs_service@localhost:5432/igot";jwt_secret:str="";jwt_algorithm:str="HS256";rabbitmq_url:str="amqp://guest:guest@localhost:5672//"
    docker_base_url:str="unix:///var/run/docker.sock";workspace_image:str="igot/lab-workspace:local";allowed_target_images:str="igot/target-demo:local";public_base_url:str="http://localhost:8000";default_ttl_minutes:int=45;auto_create_schema:bool=False
    controller_container_name:str="labs";execution_timeout_seconds:int=15;max_output_bytes:int=262144
    @property
    def target_allowlist(self):return {v.strip() for v in self.allowed_target_images.split(",") if v.strip()}
@lru_cache
def get_settings():return Settings()
