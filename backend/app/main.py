import os
import time
import uuid
import secrets
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import init_db, SessionLocal, get_db
from backend.app.core.logging import setup_structured_logging, scrub_sensitive_data
from backend.app.core.metrics import metrics_registry
from backend.app.core.rate_limiter import RateLimiterMiddleware, limiter
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

# Initialize structured JSON logging
setup_structured_logging()
logger = logging.getLogger("kalyan.core")

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
            admin_pwd = settings.ADMIN_BOOTSTRAP_PASSWORD
            must_change = False
            if not admin_pwd:
                if settings.ENVIRONMENT == "production":
                    raise RuntimeError("FATAL: ADMIN_BOOTSTRAP_PASSWORD environment variable must be set in production.")
                admin_pwd = "admin123" if settings.ENVIRONMENT == "test" else secrets.token_urlsafe(16)
                must_change = (settings.ENVIRONMENT != "test")
                logger.info(f"[BOOTSTRAP] Initialized default admin account. must_change_password={must_change}")

            admin_user = User(
                id="admin-master-id",
                email="admin@kalyan-ai.internal",
                username="admin",
                hashed_password=get_password_hash(admin_pwd),
                role=UserRole.ADMIN,
                is_active=True,
                personalization_enabled=True,
                must_change_password=must_change
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
            op_pwd = settings.OPERATOR_BOOTSTRAP_PASSWORD
            must_change = False
            if not op_pwd:
                if settings.ENVIRONMENT == "production":
                    raise RuntimeError("FATAL: OPERATOR_BOOTSTRAP_PASSWORD environment variable must be set in production.")
                op_pwd = "operator123" if settings.ENVIRONMENT == "test" else secrets.token_urlsafe(16)
                must_change = (settings.ENVIRONMENT != "test")
                logger.info(f"[BOOTSTRAP] Initialized default operator account. must_change_password={must_change}")

            operator_user = User(
                id="operator-master-id",
                email="operator@kalyan-ai.internal",
                username="operator",
                hashed_password=get_password_hash(op_pwd),
                role=UserRole.OPERATOR,
                is_active=True,
                personalization_enabled=True,
                must_change_password=must_change
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

# Request context & observability middleware
class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = req_id
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        path = request.url.path

        # Record metric and trace
        if path.startswith("/api/"):
            metrics_registry.record_request(
                endpoint=path,
                status_code=response.status_code,
                duration_sec=duration
            )

        response.headers["x-request-id"] = req_id
        return response

app.add_middleware(ObservabilityMiddleware)
app.add_middleware(RateLimiterMiddleware, behind_trusted_proxy=False)

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

@app.get("/metrics")
def get_prometheus_metrics(db: Session = Depends(get_db)):
    content = metrics_registry.render_prometheus(db)
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")

# Mount static frontend build if present for unified fullstack hosting
frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="static_assets")

    @app.get("/{full_path:path}")
    async def serve_frontend_spa(full_path: str):
        # Don't intercept API paths or metrics
        if full_path.startswith("api/") or full_path.startswith("health") or full_path.startswith("metrics"):
            return None
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))
