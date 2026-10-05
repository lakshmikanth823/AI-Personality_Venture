from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Boolean, Float
from backend.app.core.database import Base

class ModerationResult(Base):
    __tablename__ = "moderation_results"

    id = Column(String(36), primary_key=True, index=True)
    entity_type = Column(String(32), nullable=False) # "message", "candidate", "prompt"
    entity_id = Column(String(36), nullable=False, index=True)
    policy_flag = Column(String(64), default="clean", nullable=False) # clean, harassment, hate, sexual, self_harm, defamation, political, prompt_injection, pii_leak
    risk_tier = Column(String(16), default="tier_0", nullable=False) # tier_0, tier_1, tier_2, tier_3
    risk_score = Column(Float, default=0.0)
    reasoning = Column(Text, nullable=True)
    action_taken = Column(String(32), default="allow", nullable=False) # allow, review_queue, blocked
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, index=True)
    actor_id = Column(String(64), nullable=False, index=True) # user_id, operator_id, or "system"
    actor_role = Column(String(32), default="system")
    action = Column(String(64), nullable=False) # "publish", "approve", "reject", "kill_switch_engaged", "memory_deleted", etc.
    target_type = Column(String(64), nullable=True)
    target_id = Column(String(64), nullable=True)
    details_json = Column(Text, default="{}")
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class KillSwitchState(Base):
    __tablename__ = "kill_switch_state"

    id = Column(String(36), primary_key=True, index=True)
    is_active = Column(Boolean, default=False, nullable=False)
    activated_by = Column(String(64), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=True)
    deactivated_by = Column(String(64), nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
