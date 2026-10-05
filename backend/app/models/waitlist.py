import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from backend.app.core.database import Base

class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(32), nullable=True)
    queue_position = Column(Integer, nullable=False)
    referral_code = Column(String(64), nullable=True)
    status = Column(String(32), default="waiting", nullable=False) # waiting, invited, admitted
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
