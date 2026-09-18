from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from igot_competency.api.routes import router
from igot_competency.config import settings
app=FastAPI(title="iGOT Competency Service",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=list(settings.cors_origins),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)
@app.get("/health")
def health(): return {"status":"ok","service":"competency"}
