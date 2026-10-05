from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.experiment_engine import ExperimentEngine

router = APIRouter(prefix="/experiments", tags=["experiments"])

@router.get("/")
def get_experiments(db: Session = Depends(get_db)):
    engine = ExperimentEngine(db)
    return engine.get_active_experiments()
