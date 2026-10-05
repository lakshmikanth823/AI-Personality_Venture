from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# Normalize database URL for synchronous SQLAlchemy engine
sync_db_url = settings.DATABASE_URL
if sync_db_url.startswith("postgresql+asyncpg://"):
    sync_db_url = sync_db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)

connect_args = {}
engine_kwargs = {"echo": False}

if sync_db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
else:
    # PostgreSQL connection pool settings
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(sync_db_url, **engine_kwargs)

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
