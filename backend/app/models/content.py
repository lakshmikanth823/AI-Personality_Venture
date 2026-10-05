from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class ContentCandidate(Base):
    __tablename__ = "content_candidates"

    id = Column(String(36), primary_key=True, index=True)
    source_channel = Column(String(32), default="x", nullable=False) # x, instagram, youtube, whatsapp, web
    pillar = Column(String(64), nullable=False) # indian_internet_life, college_job, relationships, ai_tech, cricket_pop, user_situations, character_lore
    format = Column(String(32), nullable=False) # reply, observation, situation, series, lore
    raw_prompt = Column(Text, nullable=False)
    candidate_text = Column(Text, nullable=False)
    risk_tier = Column(String(16), default="tier_0", nullable=False) # tier_0, tier_1, tier_2, tier_3
    safety_evaluation_json = Column(Text, default="{}")
    status = Column(String(32), default="pending_approval", nullable=False) # draft, pending_approval, approved, rejected, published
    operator_notes = Column(Text, nullable=True)
    scheduled_for = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    approvals = relationship("Approval", back_populates="candidate", cascade="all, delete-orphan")
    published_actions = relationship("PublishedAction", back_populates="candidate", cascade="all, delete-orphan")

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, index=True)
    candidate_id = Column(String(36), ForeignKey("content_candidates.id", ondelete="CASCADE"), nullable=False)
    operator_id = Column(String(36), nullable=False)
    action = Column(String(32), nullable=False) # approved, rejected, edited
    original_text = Column(Text, nullable=False)
    final_text = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    candidate = relationship("ContentCandidate", back_populates="approvals")

class PublishedAction(Base):
    __tablename__ = "published_actions"

    id = Column(String(36), primary_key=True, index=True)
    candidate_id = Column(String(36), ForeignKey("content_candidates.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(32), nullable=False) # x, instagram, youtube, whatsapp
    external_post_id = Column(String(128), nullable=True)
    published_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    payload_json = Column(Text, default="{}")
    status = Column(String(32), default="success", nullable=False) # success, failed, cancelled_by_kill_switch
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    candidate = relationship("ContentCandidate", back_populates="published_actions")

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(String(36), primary_key=True, index=True)
    platform = Column(String(32), nullable=False) # x, instagram, youtube, whatsapp
    handle = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    rate_limit_per_hour = Column(Integer, default=30)
    current_usage_hour = Column(Integer, default=0)
    last_reset = Column(DateTime, default=lambda: datetime.now(timezone.utc))
