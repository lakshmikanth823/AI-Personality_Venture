import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.core.database import Base, get_db, engine, SessionLocal as TestingSessionLocal
from backend.app.main import app
from backend.app.models.user import User, Profile, UserRole
from backend.app.models.character import CharacterVersion, CharacterLore
from backend.app.services.persona_engine import KALYAN_CONSTITUTION
from backend.app.core.security import get_password_hash
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.rate_limiter import limiter
settings.ENVIRONMENT = "test"
settings.APP_ENV = "test"
settings.DEFAULT_PROVIDER = "mock"

@pytest.fixture(scope="function", autouse=True)
def db_session():
    from backend.app.core.database import init_db
    init_db()
    session = TestingSessionLocal()
    
    # Seed default admin & operator
    admin = User(
        id="admin-master-id",
        email="admin@kalyan-ai.internal",
        username="admin",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
        personalization_enabled=True
    )
    session.add(admin)
    
    operator = User(
        id="operator-master-id",
        email="operator@kalyan-ai.internal",
        username="operator",
        hashed_password=get_password_hash("operator123"),
        role=UserRole.OPERATOR,
        is_active=True,
        personalization_enabled=True
    )
    session.add(operator)

    # Seed Guest User
    guest = User(
        id="guest_user",
        email="guest@kalyan-ai.internal",
        username="guest_user",
        hashed_password=get_password_hash("guest123"),
        role=UserRole.USER,
        is_active=True,
        personalization_enabled=False
    )
    session.add(guest)

    # Seed default character
    char = CharacterVersion(
        id="kalyan-canon-v1",
        version_tag="v1.0-public-canon",
        name="Kalyan",
        archetype="The brutally honest Indian internet friend",
        tagline="Zero corporate sugarcoating, 100% filterless reality.",
        system_prompt=KALYAN_CONSTITUTION,
        is_active=True
    )
    session.add(char)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    limiter.reset()
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    limiter.reset()
