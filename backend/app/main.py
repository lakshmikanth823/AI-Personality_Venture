from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import init_db, SessionLocal
from backend.app.services.persona_engine import PersonaEngine
from backend.app.services.experiment_engine import ExperimentEngine
from backend.app.services.kill_switch import KillSwitchManager
from backend.app.core.security import get_password_hash
from backend.app.models.user import User, Profile, UserRole
from backend.app.models.character import CharacterVersion

# Routers
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.memories import router as memories_router
from backend.app.api.v1.approval import router as approval_router
from backend.app.api.v1.publisher import router as publisher_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.experiments import router as experiments_router
from backend.app.api.v1.subscriptions import router as subscriptions_router
from backend.app.api.v1.admin import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database schema
    init_db()

    # 2. Seed initial canonical data
    db = SessionLocal()
    try:
        # Seed Kalyan Persona
        p_engine = PersonaEngine(db)
        p_engine.get_or_create_default_character()

        # Seed Experiments
        e_engine = ExperimentEngine(db)

        # Seed Kill Switch state
        k_mgr = KillSwitchManager(db)

        # Seed Default Operator and Admin users if not existing
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                id="admin-master-id",
                email="admin@kalyan-ai.internal",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
                personalization_enabled=True
            )
            db.add(admin_user)
            db.flush()
            admin_profile = Profile(
                id="admin-profile-id",
                user_id=admin_user.id,
                display_name="Kalyan Ops Lead",
                preferred_language="hinglish"
            )
            db.add(admin_profile)

        operator_user = db.query(User).filter(User.username == "operator").first()
        if not operator_user:
            operator_user = User(
                id="operator-master-id",
                email="operator@kalyan-ai.internal",
                username="operator",
                hashed_password=get_password_hash("operator123"),
                role=UserRole.OPERATOR,
                is_active=True,
                personalization_enabled=True
            )
            db.add(operator_user)
            db.flush()
            operator_profile = Profile(
                id="operator-profile-id",
                user_id=operator_user.id,
                display_name="Social Moderator",
                preferred_language="hinglish"
            )
            db.add(operator_profile)

        db.commit()
    finally:
        db.close()

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(memories_router, prefix=settings.API_V1_STR)
app.include_router(approval_router, prefix=settings.API_V1_STR)
app.include_router(publisher_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(experiments_router, prefix=settings.API_V1_STR)
app.include_router(subscriptions_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "kalyan-personality-backend",
        "version": settings.VERSION,
        "character": "Kalyan",
        "archetype": "The brutally honest Indian internet friend"
    }

# Mount static frontend build if present for unified fullstack hosting
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="static_assets")

    @app.get("/{full_path:path}")
    async def serve_frontend_spa(full_path: str):
        # Don't intercept API paths
        if full_path.startswith("api/") or full_path.startswith("health"):
            return None
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))

