from pathlib import Path
from .config import get_settings
class LocalStorage:
    def put(self,key:str,data:bytes)->str:
        root=Path(get_settings().artifact_storage_root).resolve();target=(root/key).resolve()
        if root not in target.parents:raise ValueError("invalid artifact key")
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);return f"local://{key}"
class SupabaseStorage:
    def __init__(self):
        from supabase import create_client
        cfg=get_settings();self.bucket=cfg.supabase_bucket;self.client=create_client(cfg.supabase_url,cfg.supabase_service_key)
    def put(self,key:str,data:bytes)->str:self.client.storage.from_(self.bucket).upload(key,data,{"upsert":"true"});return f"supabase://{self.bucket}/{key}"
def storage():return SupabaseStorage() if get_settings().storage_backend=="supabase" else LocalStorage()
