from typing import Optional
from pydantic import BaseModel

class CandidateGenerateRequest(BaseModel):
    count: int = 5
    channel: str = "x"

class ApprovalAction(BaseModel):
    action: str # "approved", "rejected", "edited"
    final_text: Optional[str] = None
    reason: Optional[str] = None

class PublishRequest(BaseModel):
    channel: Optional[str] = None
