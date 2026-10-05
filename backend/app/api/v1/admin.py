from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.safety import AuditLog
from backend.app.models.character import CharacterLore, CharacterVersion
from backend.app.api.deps import require_role
from backend.app.services.kill_switch import KillSwitchManager

router = APIRouter(prefix="/admin", tags=["admin"])

class KillSwitchActionPayload(BaseModel):
    reason: str

class LoreCreatePayload(BaseModel):
    title: str
    content: str
    category: str = "origin"
    lore_type: str = "canon" # "canon" | "improvisation" | "community"

@router.get("/kill-switch/status")
def get_kill_switch_status(db: Session = Depends(get_db)):
    mgr = KillSwitchManager(db)
    return mgr.get_status()

@router.post("/kill-switch/activate")
def activate_kill_switch(
    payload: KillSwitchActionPayload,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    mgr = KillSwitchManager(db)
    return mgr.activate(actor_id=current_user.id, reason=payload.reason)

@router.post("/kill-switch/deactivate")
def deactivate_kill_switch(
    payload: KillSwitchActionPayload,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    mgr = KillSwitchManager(db)
    return mgr.deactivate(actor_id=current_user.id, reason=payload.reason)

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "actor_id": l.actor_id,
            "actor_role": l.actor_role,
            "action": l.action,
            "target_type": l.target_type,
            "target_id": l.target_id,
            "details": l.details_json,
            "timestamp": l.timestamp.isoformat()
        }
        for l in logs
    ]

@router.get("/lore")
def list_lore(db: Session = Depends(get_db)):
    lores = db.query(CharacterLore).filter(CharacterLore.is_active == True).order_by(CharacterLore.created_at.desc()).all()
    return [
        {
            "id": l.id,
            "title": l.title,
            "content": l.content,
            "category": l.category,
            "lore_type": l.lore_type,
            "is_verified_canon": l.is_verified_canon,
            "created_at": l.created_at.isoformat()
        }
        for l in lores
    ]

@router.post("/lore")
def create_lore(
    payload: LoreCreatePayload,
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    char_version = db.query(CharacterVersion).filter(CharacterVersion.is_active == True).first()
    version_id = char_version.id if char_version else "kalyan-canon-v1"
    
    import uuid
    from datetime import datetime, timezone
    new_lore = CharacterLore(
        id=str(uuid.uuid4()),
        character_version_id=version_id,
        lore_type=payload.lore_type,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        is_verified_canon=(payload.lore_type == "canon"),
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_lore)
    db.commit()
    return {"status": "created", "lore_id": new_lore.id, "title": new_lore.title}
