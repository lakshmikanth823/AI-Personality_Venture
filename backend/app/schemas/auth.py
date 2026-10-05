from typing import Optional
from pydantic import BaseModel, EmailStr

class UserSignup(BaseModel):
    email: EmailStr
    username: str
    password: str
    display_name: Optional[str] = None
    preferred_language: Optional[str] = "hinglish"

class UserLogin(BaseModel):
    email_or_username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str

class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    role: str
    display_name: str
    preferred_language: str
    personalization_enabled: bool
