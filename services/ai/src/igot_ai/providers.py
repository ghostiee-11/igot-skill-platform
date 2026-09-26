import json,re
import httpx
from .config import get_settings
class ProviderUnavailable(RuntimeError):pass
class MultiProvider:
    def __init__(self,client:httpx.AsyncClient|None=None):self.client=client
    async def complete(self,messages:list[dict],preferred:str|None=None)->dict:
        cfg=get_settings(); order=[p.strip() for p in cfg.provider_order.split(",") if p.strip()]
        if preferred in order:order.remove(preferred);order.insert(0,preferred)
        failures=[]
        if self.client is not None:
            return await self._try_providers(self.client, order, messages, failures)
        async with httpx.AsyncClient(timeout=30) as client:
            return await self._try_providers(client, order, messages, failures)

    async def _try_providers(self,client,order,messages,failures):
        for provider in order:
            try:
                value=await self._call(client,provider,messages)
                if value:return {"provider":provider,"content":value}
            except (httpx.HTTPError,KeyError,ValueError) as exc:failures.append(f"{provider}:{type(exc).__name__}")
        raise ProviderUnavailable(", ".join(failures) or "no AI provider configured")
    async def _call(self,client,provider,messages):
        cfg=get_settings()
        if provider in {"groq","nim","openai"}:
            key=getattr(cfg,f"{provider}_api_key");model=getattr(cfg,f"{provider}_model")
            if not key:raise ValueError("missing key")
            url={"groq":"https://api.groq.com/openai/v1/chat/completions","nim":"https://integrate.api.nvidia.com/v1/chat/completions","openai":"https://api.openai.com/v1/chat/completions"}[provider]
            res=await client.post(url,headers={"Authorization":f"Bearer {key}"},json={"model":model,"messages":messages,"temperature":0.2});res.raise_for_status();return res.json()["choices"][0]["message"]["content"]
        if provider=="gemini":
            if not cfg.gemini_api_key:raise ValueError("missing key")
            prompt="\n".join(f"{m.get('role','user')}: {m.get('content','')}" for m in messages);url=f"https://generativelanguage.googleapis.com/v1beta/models/{cfg.gemini_model}:generateContent?key={cfg.gemini_api_key}"
            res=await client.post(url,json={"contents":[{"parts":[{"text":prompt}]}]});res.raise_for_status();return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        raise ValueError("unsupported provider")
def extract_json(value:str):
    value=re.sub(r"^```(?:json)?\s*|\s*```$","",value.strip(),flags=re.I|re.S);start=value.find("{");end=value.rfind("}")
    if start<0 or end<start:raise ValueError("model response did not contain a JSON object")
    return json.loads(value[start:end+1])
