from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user
from backend.app.services.memory_engine import MemoryEngine

router = APIRouter(prefix="/memories", tags=["memories"])

@router.get("", response_model=List[Dict[str, Any]], include_in_schema=False)
@router.get("/", response_model=List[Dict[str, Any]])
def list_user_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = MemoryEngine(db)
    return engine.list_user_memories(current_user.id)

@router.delete("/{memory_id}")
def delete_single_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = MemoryEngine(db)
    success = engine.delete_memory(current_user.id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found or already deleted")
    return {"status": "success", "message": "Memory item removed. Kalyan will no longer factor this fact into future conversations."}

@router.delete("/clear/all")
def clear_all_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = MemoryEngine(db)
    count = engine.clear_all_memories(current_user.id)
    return {"status": "success", "deleted_count": count, "message": "All durable memories wiped successfully."}

@router.get("/export/privacy-data")
def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = MemoryEngine(db)
    memories = engine.list_user_memories(current_user.id)
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "personalization_enabled": current_user.personalization_enabled,
        "stored_memories": memories,
        "conversation_count": len(current_user.conversations),
        "exported_at": "now"
    }
