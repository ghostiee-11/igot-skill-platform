from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
import threading
from app.core.database import engine, Base, SessionLocal, warm_connection_pool
from app.core.seed_data import seed_database
from app.core.seed_competencies import seed_competency_taxonomy, seed_evidence_mapping, seed_demo_usage_evidence, users_with_placeholder_gaps
from app.agents.competency.gap_agent import run_gap_analysis

# Import routers
from app.modules.digital_governance.router import router as digital_governance_router
from app.modules.auth.router import router as auth_router
from app.modules.onboarding.router import router as onboarding_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.discover.router import router as discover_router
from app.modules.courses.router import router as courses_router
from app.modules.learning.router import router as learning_router
from app.modules.assessments.router import router as assessments_router
from app.modules.profile.router import router as profile_router
from app.modules.admin.router import router as admin_router
from app.agents.router import router as agents_router
from app.statistical_engine.api.router import router as stats_engine_router
from app.modules.behavioural_cgp.router import router as behavioural_router
from app.modules.technical_courses.router import router as technical_courses_router
from app.modules.competency.router import router as competency_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.quiz.router import router as quiz_router

# Create DB tables
Base.metadata.create_all(bind=engine)

# Seed database on startup
db = SessionLocal()
try:
    seed_database(db)
    seed_competency_taxonomy(db)
    seed_evidence_mapping(db)
    refreshed_users = set(seed_demo_usage_evidence(db)) | set(users_with_placeholder_gaps(db))
    for user_id in refreshed_users:
        run_gap_analysis(db, user_id)
finally:
    db.close()

# Open pooled database connections in the background so the first page loads skip the connection cost.
threading.Thread(target=warm_connection_pool, daemon=True).start()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Phase 0 API for iGot Karmayogi AI-Enabled Skill Intelligence & Learning Platform",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for easy development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount domain routers
app.include_router(digital_governance_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(onboarding_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(discover_router, prefix=settings.API_V1_STR)
app.include_router(courses_router, prefix=settings.API_V1_STR)
app.include_router(learning_router, prefix=settings.API_V1_STR)
app.include_router(assessments_router, prefix=settings.API_V1_STR)
app.include_router(profile_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(competency_router, prefix=settings.API_V1_STR)
app.include_router(recommendations_router, prefix=settings.API_V1_STR)
app.include_router(quiz_router, prefix=settings.API_V1_STR)
# Statistical Engine & Adaptive Branching Exam
app.include_router(stats_engine_router, prefix="/api/v1")
app.include_router(stats_engine_router, prefix="/api")
app.include_router(stats_engine_router, prefix=settings.API_V1_STR)

# Behavioural Pipeline & AI Live Oral Board
app.include_router(behavioural_router, prefix="/api/v1")
app.include_router(behavioural_router, prefix="/api")
app.include_router(behavioural_router, prefix=settings.API_V1_STR)

# Technical Course Pipeline & Hands-on Labs
app.include_router(technical_courses_router, prefix="/api/v1")
app.include_router(technical_courses_router, prefix="/api")
app.include_router(technical_courses_router, prefix=settings.API_V1_STR)

# Digital Governance & Cybersecurity Sandbox
app.include_router(digital_governance_router, prefix="/api/v1")
app.include_router(digital_governance_router, prefix="/api")
app.include_router(digital_governance_router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "iGot Karmayogi Backend",
        "version": "Phase 0 - 2026",
        "ai_agent_ready": True
    }
