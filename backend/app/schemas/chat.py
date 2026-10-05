from typing import Optional, List
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    language_preference: Optional[str] = "hinglish" # "english", "hinglish", "telugu_hinglish"
    channel: Optional[str] = "web"

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
