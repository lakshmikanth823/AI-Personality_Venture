from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Memory(Base):
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    memory_type = Column(String(32), nullable=False) # "l2_summary" | "l3_durable_fact"
    category = Column(String(64), default="preference") # "preference", "biographical", "humor_reaction", "topic_interest"
    key = Column(String(128), nullable=False, index=True)
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    source_message_id = Column(String(36), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False) # User privacy deletion
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="memories")
