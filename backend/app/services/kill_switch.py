import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.safety import KillSwitchState, AuditLog

class KillSwitchManager:
    _instance = None
    _in_memory_state: bool = False

    def __init__(self, db: Session):
        self.db = db
        self._sync_state()

    def _sync_state(self):
        state_record = self.db.query(KillSwitchState).first()
        if not state_record:
            state_record = KillSwitchState(
                id="global-kill-switch-1",
                is_active=False
            )
            self.db.add(state_record)
            self.db.commit()
            self.db.refresh(state_record)
        self._in_memory_state = state_record.is_active

    def is_kill_switch_active(self) -> bool:
        state_record = self.db.query(KillSwitchState).first()
        if state_record:
            self._in_memory_state = state_record.is_active
            return state_record.is_active
        return False

    def is_active(self, scope: str = "global") -> bool:
        return self.is_kill_switch_active()

    def can_publish(self) -> bool:
        return not self.is_kill_switch_active()

    def activate(self, actor_id: str, reason: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        state_record = self.db.query(KillSwitchState).first()
        if not state_record:
            state_record = KillSwitchState(id="global-kill-switch-1")
            self.db.add(state_record)

        state_record.is_active = True
        state_record.activated_by = actor_id
        state_record.activated_at = datetime.now(timezone.utc)
        state_record.reason = reason
        self._in_memory_state = True

        audit = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=actor_id,
            actor_role="admin",
            action="KILL_SWITCH_ACTIVATED",
            target_type="system",
            target_id="publisher_and_autonomous_engine",
            details_json=f'{{"reason": "{reason}", "action": "HALT_ALL_PUBLISHING"}}',
            ip_address=ip_address
        )
        self.db.add(audit)
        self.db.commit()

        return {
            "status": "engaged",
            "is_active": True,
            "activated_by": actor_id,
            "activated_at": state_record.activated_at.isoformat(),
            "reason": reason,
            "message": "EMERGENCY KILL SWITCH ENGAGED. All external publishing, autonomous worker jobs, and social channel dispatchers are strictly halted."
        }

    def deactivate(self, actor_id: str, reason: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        state_record = self.db.query(KillSwitchState).first()
        if state_record:
            state_record.is_active = False
            state_record.deactivated_by = actor_id
            state_record.deactivated_at = datetime.now(timezone.utc)
            self._in_memory_state = False

            audit = AuditLog(
                id=str(uuid.uuid4()),
                actor_id=actor_id,
                actor_role="admin",
                action="KILL_SWITCH_DEACTIVATED",
                target_type="system",
                target_id="publisher_and_autonomous_engine",
                details_json=f'{{"reason": "{reason}", "action": "RESTORE_PUBLISHING"}}',
                ip_address=ip_address
            )
            self.db.add(audit)
            self.db.commit()

        return {
            "status": "disengaged",
            "is_active": False,
            "deactivated_by": actor_id,
            "reason": reason,
            "message": "Kill switch disengaged. Publishing services restored under normal human-in-the-loop governance."
        }

    def get_status(self) -> Dict[str, Any]:
        state_record = self.db.query(KillSwitchState).first()
        if not state_record:
            return {"is_active": False}
        return {
            "is_active": state_record.is_active,
            "activated_by": state_record.activated_by,
            "activated_at": state_record.activated_at.isoformat() if state_record.activated_at else None,
            "reason": state_record.reason
        }
