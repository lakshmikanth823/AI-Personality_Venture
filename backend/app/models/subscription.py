from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, Boolean
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_tier = Column(String(32), default="free", nullable=False) # free, single_roast_49, fan_pass_149, vip_insider_299, custom_lore_999
    status = Column(String(32), default="active", nullable=False) # active, expired, cancelled
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    total_paid_inr = Column(Float, default=0.0)
    perks_json = Column(Text, default="{}")

    user = relationship("User", back_populates="subscriptions")
    transactions = relationship("PaymentTransaction", back_populates="subscription", cascade="all, delete-orphan")

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(String(36), primary_key=True, index=True)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_tier = Column(String(32), nullable=False)
    amount_inr = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    status = Column(String(32), default="completed", nullable=False) # pending, completed, failed, refunded
    payment_reference = Column(String(128), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    subscription = relationship("Subscription", back_populates="transactions")
