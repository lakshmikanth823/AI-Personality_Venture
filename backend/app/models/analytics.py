from datetime import datetime, timezone, date
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, Date
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    feature_name = Column(String(64), nullable=False) # "web_chat", "social_reply", "content_generation", "share_card"
    model_name = Column(String(64), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="usage_events")

class CostEvent(Base):
    __tablename__ = "cost_events"

    id = Column(String(36), primary_key=True, index=True)
    category = Column(String(64), nullable=False) # "inference", "moderation", "database", "social_api"
    amount_usd = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id = Column(String(36), primary_key=True, index=True)
    metric_date = Column(Date, default=date.today, unique=True, index=True, nullable=False)
    dau = Column(Integer, default=0)
    wau = Column(Integer, default=0)
    wmcr = Column(Integer, default=0) # Weekly Meaningful Character Relationships (>=3 interactions/7d)
    total_messages = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    impressions_count = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    total_revenue_inr = Column(Float, default=0.0)
    safety_incidents = Column(Integer, default=0)
