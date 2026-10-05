import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.waitlist import WaitlistEntry

router = APIRouter(prefix="/waitlist", tags=["waitlist"])

class WaitlistRequest(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    referral_code: Optional[str] = None

class WaitlistResponse(BaseModel):
    status: str
    email: str
    queue_position: int
    estimated_cohort: str
    message: str

@router.post("", response_model=WaitlistResponse)
def join_waitlist(data: WaitlistRequest, db: Session = Depends(get_db)):
    # 1. Deduplication check
    existing = db.query(WaitlistEntry).filter(WaitlistEntry.email == data.email).first()
    if existing:
        return WaitlistResponse(
            status="already_registered",
            email=existing.email,
            queue_position=existing.queue_position,
            estimated_cohort="Beta Cohort 2",
            message=f"You are already on the Kalyan waitlist at position #{existing.queue_position}."
        )

    # 2. Compute FIFO queue position
    position = db.query(WaitlistEntry).count() + 1

    entry = WaitlistEntry(
        id=str(uuid.uuid4()),
        email=data.email,
        phone=data.phone,
        queue_position=position,
        referral_code=data.referral_code,
        status="waiting"
    )
    db.add(entry)
    db.commit()

    return WaitlistResponse(
        status="queued",
        email=entry.email,
        queue_position=position,
        estimated_cohort="Beta Cohort 2",
        message=f"Spot reserved! You are #{position} in line for Kalyan's next beta cohort."
    )

@router.get("/status/{email}", response_model=WaitlistResponse)
def get_waitlist_status(email: str, db: Session = Depends(get_db)):
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.email == email).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Email not found on waitlist.")

    return WaitlistResponse(
        status=entry.status,
        email=entry.email,
        queue_position=entry.queue_position,
        estimated_cohort="Beta Cohort 2",
        message=f"Current position: #{entry.queue_position}"
    )
