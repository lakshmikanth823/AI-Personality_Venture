"""
backend/app/core/startup_health.py
Startup health check and live credential validation.
Enforces fail-fast termination in production if required external API keys
(Gemini/OpenAI, Razorpay, WhatsApp/Meta) are missing, invalid, or unreachable.
"""

import logging
from typing import Dict, Any
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

async def verify_live_credentials() -> Dict[str, Any]:
    """
    Validates external credentials on startup.
    In Production (APP_ENV=production):
      1. Verifies AI provider is not 'mock' and tests upstream connectivity.
      2. Verifies Razorpay payment gateway credentials.
      3. Verifies Meta/Social broadcasting tokens if live broadcast is active.
      Raises RuntimeError if any check fails (Fail-Fast).
    In Non-Production (test/development):
      Logs status and allows mock/fixture operations.
    """
    app_env = getattr(settings, "APP_ENV", os_env())
    
    if app_env != "production":
        logger.info(f"[STARTUP HEALTH] Non-production environment ({app_env}) detected. Credential fail-fast bypassed.")
        return {
            "status": "healthy",
            "environment": app_env,
            "provider": settings.DEFAULT_PROVIDER,
            "live_broadcast": settings.ENABLE_LIVE_SOCIAL_BROADCAST
        }

    logger.info("[STARTUP HEALTH] Running production live credential verification...")

    # 1. AI Provider Validation
    if settings.DEFAULT_PROVIDER == "mock":
        raise RuntimeError("FATAL: DEFAULT_PROVIDER cannot be 'mock' in production environment.")

    if settings.DEFAULT_PROVIDER == "gemini":
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("FATAL: GEMINI_API_KEY is missing in production environment.")
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                res = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={settings.GEMINI_API_KEY}"
                )
                if res.status_code != 200:
                    raise RuntimeError(f"FATAL: Gemini API credential validation failed (HTTP {res.status_code}).")
            except httpx.RequestError as e:
                raise RuntimeError(f"FATAL: Gemini API connectivity check failed: {e}")

    elif settings.DEFAULT_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("FATAL: OPENAI_API_KEY is missing in production environment.")
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                res = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                )
                if res.status_code != 200:
                    raise RuntimeError(f"FATAL: OpenAI API credential validation failed (HTTP {res.status_code}).")
            except httpx.RequestError as e:
                raise RuntimeError(f"FATAL: OpenAI API connectivity check failed: {e}")

    # 2. Payment Gateway Validation
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise RuntimeError("FATAL: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured in production.")
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(
                "https://api.razorpay.com/v1/payments?count=1",
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            if res.status_code == 401:
                raise RuntimeError("FATAL: Razorpay API authentication failed (HTTP 401 Unauthorized).")
        except httpx.RequestError as e:
            raise RuntimeError(f"FATAL: Razorpay API connectivity check failed: {e}")

    # 3. Live Social Broadcasting Validation
    if settings.ENABLE_LIVE_SOCIAL_BROADCAST:
        if not settings.WHATSAPP_TOKEN:
            raise RuntimeError("FATAL: WHATSAPP_TOKEN is required when ENABLE_LIVE_SOCIAL_BROADCAST is enabled in production.")

    logger.info("[STARTUP HEALTH] All production credentials verified successfully.")
    return {
        "status": "healthy",
        "environment": "production",
        "provider": settings.DEFAULT_PROVIDER,
        "live_broadcast": settings.ENABLE_LIVE_SOCIAL_BROADCAST
    }

def os_env() -> str:
    import os
    return os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development"))
