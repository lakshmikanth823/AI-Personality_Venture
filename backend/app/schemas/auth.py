from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserSignup(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)
    display_name: Optional[str] = None
    preferred_language: Optional[str] = "hinglish"
    consent_given: bool = True  # DPDP Act 2023 consent capture

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Username cannot be empty or whitespace only")
        return v.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

class UserLogin(BaseModel):
    email_or_username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    totp_code: Optional[str] = None

    @field_validator("email_or_username")
    @classmethod
    def clean_identifier(cls, v: str) -> str:
        return v.strip()

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str
    mfa_required: bool = False
    mfa_authenticated: bool = False
    must_change_password: bool = False

class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None

class MFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    qr_code_hint: str

class MFAVerifyRequest(BaseModel):
    code: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    role: str
    display_name: str
    preferred_language: str
    personalization_enabled: bool
    mfa_enabled: bool = False
    must_change_password: bool = False
