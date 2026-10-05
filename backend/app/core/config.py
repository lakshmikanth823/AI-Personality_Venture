import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    PROJECT_NAME: str = "Kalyan — AI Personality Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-kalyan-personality-venture-production-ready-2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./kalyan_personality.db")
    
    # AI Providers & Model Configuration
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "mock") # "mock" | "gemini" | "openai" | "anthropic"
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    
    # Social Broadcasting & Live API Configuration
    ENABLE_LIVE_SOCIAL_BROADCAST: bool = os.getenv("ENABLE_LIVE_SOCIAL_BROADCAST", "false").lower() in ["true", "1", "yes"]
    X_API_KEY: Optional[str] = os.getenv("X_API_KEY", None)
    X_API_SECRET: Optional[str] = os.getenv("X_API_SECRET", None)
    X_ACCESS_TOKEN: Optional[str] = os.getenv("X_ACCESS_TOKEN", None)
    X_ACCESS_SECRET: Optional[str] = os.getenv("X_ACCESS_SECRET", None)
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = os.getenv("INSTAGRAM_ACCESS_TOKEN", None)
    INSTAGRAM_PAGE_ID: Optional[str] = os.getenv("INSTAGRAM_PAGE_ID", None)
    YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY", None)
    WHATSAPP_TOKEN: Optional[str] = os.getenv("WHATSAPP_TOKEN", None)
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = os.getenv("WHATSAPP_PHONE_NUMBER_ID", None)
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "kalyan_wa_verify_2026")

    # Payment Gateway Configuration
    RAZORPAY_KEY_ID: Optional[str] = os.getenv("RAZORPAY_KEY_ID", None)
    RAZORPAY_KEY_SECRET: Optional[str] = os.getenv("RAZORPAY_KEY_SECRET", None)
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "rzp_webhook_secret_kalyan_2026")

    # Operational Controls
    KILL_SWITCH_ACTIVE: bool = False
    REQUIRE_HUMAN_APPROVAL_FOR_TIER1: bool = False # Tier 1 can auto-draft; Tier 2 strictly human approval
    
    # Financial & Unit Economics Telemetry
    COST_PER_1K_INPUT_TOKENS_USD: float = 0.0005
    COST_PER_1K_OUTPUT_TOKENS_USD: float = 0.0015
    INR_PER_USD: float = 86.0
    
    DAILY_COST_BUDGET_USD: float = float(os.getenv("DAILY_COST_BUDGET_USD", "50.0"))

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
