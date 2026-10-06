from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=50000)
    conversation_id: Optional[str] = None
    guest_session_id: Optional[str] = None
    language_preference: Optional[str] = "hinglish" # "english", "hinglish", "telugu_hinglish"
    channel: Optional[str] = "web"

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: str = "assistant"
    content: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    cost_usd: float
    risk_tier: str
    detected_policy: str
    memory_created: Optional[str] = None

class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: str

class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: str
    messages: List[MessageItem]
