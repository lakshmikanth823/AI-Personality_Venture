"""
Startup Health & Credential Validation Test Suite (Phase 5.4)
Verifies:
1. Non-production (test/dev) bypass allows smooth testing.
2. Production fail-fast triggers if DEFAULT_PROVIDER=mock.
3. Production fail-fast triggers if Gemini/OpenAI key is missing.
4. Production fail-fast triggers if Razorpay credentials are missing.
5. Production healthy startup when valid upstream responses are received.
"""

import pytest
import httpx
from backend.app.core.config import settings
from backend.app.core.startup_health import verify_live_credentials

@pytest.mark.asyncio
async def test_non_production_startup_healthy(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "test")
    res = await verify_live_credentials()
    assert res["status"] == "healthy"
    assert res["environment"] == "test"

@pytest.mark.asyncio
async def test_production_mock_provider_rejected(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "DEFAULT_PROVIDER", "mock")
    with pytest.raises(RuntimeError) as exc_info:
        await verify_live_credentials()
    assert "DEFAULT_PROVIDER cannot be 'mock' in production" in str(exc_info.value)

@pytest.mark.asyncio
async def test_production_missing_gemini_key_rejected(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "DEFAULT_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    with pytest.raises(RuntimeError) as exc_info:
        await verify_live_credentials()
    assert "GEMINI_API_KEY is missing" in str(exc_info.value)

@pytest.mark.asyncio
async def test_production_missing_razorpay_keys_rejected(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "DEFAULT_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "dummy_gemini_key")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", None)
    monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", None)

    # Mock Gemini HTTP response
    original_get = httpx.AsyncClient.get
    async def mock_get(self, url, **kwargs):
        if "generativelanguage" in str(url):
            return httpx.Response(200, json={"models": []})
        return await original_get(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(RuntimeError) as exc_info:
        await verify_live_credentials()
    assert "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured" in str(exc_info.value)

@pytest.mark.asyncio
async def test_production_all_valid_credentials_passes(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "DEFAULT_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "valid_gemini_key")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "rzp_live_123")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", "rzp_sec_456")
    monkeypatch.setattr(settings, "ENABLE_LIVE_SOCIAL_BROADCAST", False)

    # Mock upstream API calls returning 200 OK
    async def mock_get(self, url, **kwargs):
        if "generativelanguage" in str(url) or "razorpay" in str(url):
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(404)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    res = await verify_live_credentials()
    assert res["status"] == "healthy"
    assert res["environment"] == "production"
