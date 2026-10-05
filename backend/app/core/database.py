from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# Engine configuration (supporting SQLite with multi-threading or PostgreSQL)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models to ensure they are registered with Base metadata
    import backend.app.models.user
    import backend.app.models.conversation
    import backend.app.models.memory
    import backend.app.models.character
    import backend.app.models.content
    import backend.app.models.safety
    import backend.app.models.analytics
    import backend.app.models.experiment
    import backend.app.models.subscription
    
    Base.metadata.create_all(bind=engine)
