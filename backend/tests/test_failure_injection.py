"""
Failure Injection & Chaos Resilience Test Suite (G-06)
Verifies system behavior and recovery under severe failure conditions:
1. LLM Provider Timeout (HTTP 504 / asyncio.TimeoutError) -> Failover to fallback.
2. LLM Provider Rate Limiting (HTTP 429) -> Graceful failover.
3. LLM Provider Internal Server Error (HTTP 500) -> Graceful fallback.
4. Database Connection Operational Interruption -> Clean rollback and recovery.
5. Malformed JSON webhook payload -> HTTP 400 rejection without server crash.
6. Signed Payment Webhook Replay & Duplicate Attack -> Idempotency preservation.
"""

import hmac
import hashlib
import json
import uuid
import asyncio
import pytest
import httpx
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.subscription import Subscription, PaymentTransaction
from backend.app.services.model_provider import (
    AbstractModelProvider,
    ModelResponse,
    ModelRouter,
    MockModelProvider
)

client = TestClient(app)

class FailingProvider(AbstractModelProvider):
    def __init__(self, failure_mode: str):
        self.failure_mode = failure_mode

    async def generate(self, messages, system_prompt, temperature=0.7, max_tokens=600, task="chat"):
        if self.failure_mode == "timeout":
            raise asyncio.TimeoutError("Upstream LLM gateway timed out after 25.0s (HTTP 504 Gateway Timeout)")
        elif self.failure_mode == "rate_limit":
            request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
            response = httpx.Response(429, request=request, text='{"error": {"message": "Rate limit exceeded. Quota reached."}}')
            raise httpx.HTTPStatusError("429 Too Many Requests", request=request, response=response)
        elif self.failure_mode == "server_error":
            request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
            response = httpx.Response(500, request=request, text='{"error": "Internal server error"}')
            raise httpx.HTTPStatusError("500 Internal Server Error", request=request, response=response)
        raise RuntimeError("Unknown failure mode")

    async def moderate(self, text: str):
        return {"flagged": False, "risk_tier": "tier_0"}

    async def summarize(self, text: str):
        raise asyncio.TimeoutError("Summarize timed out")

    async def embed(self, text: str):
        return [0.0] * 128

    async def speak(self, text: str, voice_profile: str = "hyderabad_expressive"):
        return {"status": "failed"}


@pytest.mark.asyncio
async def test_failure_injection_provider_timeout_failover():
    """Failure Mode 1: Provider Timeout (504) -> Failover to MockModelProvider."""
    failing = FailingProvider("timeout")
    fallback = MockModelProvider()
    router = ModelRouter(primary=failing, fallback=fallback)

    messages = [{"role": "user", "content": "How do I crack an Ameerpet tech interview?"}]
    response = await router.generate(messages, system_prompt="Kalyan Constitution")

    assert response is not None
    assert len(response.content) > 10
    assert response.model_name == fallback.name
    print(f"\n[+] Timeout Failover Verified: Received response from {response.model_name}")


@pytest.mark.asyncio
async def test_failure_injection_provider_429_failover():
    """Failure Mode 2: Provider Rate Limit (429) -> Failover to MockModelProvider."""
    failing = FailingProvider("rate_limit")
    fallback = MockModelProvider()
    router = ModelRouter(primary=failing, fallback=fallback)

    messages = [{"role": "user", "content": "Tell me about Ameerpet chai."}]
    response = await router.generate(messages, system_prompt="Kalyan Constitution")

    assert response is not None
    assert response.model_name == fallback.name
    print(f"\n[+] Rate Limit (429) Failover Verified: Handled cleanly by fallback")


@pytest.mark.asyncio
async def test_failure_injection_provider_500_failover():
    """Failure Mode 3: Provider 500 Internal Server Error -> Failover to MockModelProvider."""
    failing = FailingProvider("server_error")
    fallback = MockModelProvider()
    router = ModelRouter(primary=failing, fallback=fallback)

    messages = [{"role": "user", "content": "Give me a reality check on my startup idea."}]
    response = await router.generate(messages, system_prompt="Kalyan Constitution")

    assert response is not None
    assert response.model_name == fallback.name
    print(f"\n[+] 500 Server Error Failover Verified: Fallback served valid output")


def test_failure_injection_database_operational_recovery():
    """Failure Mode 4: Database session rollback and retry resilience."""
    db = SessionLocal()
    try:
        # Simulate a transaction failure
        user_id = f"fail-db-{uuid.uuid4().hex[:6]}"
        u1 = User(id=user_id, email=f"{user_id}@kalyan.ai", username=f"db_{user_id}", hashed_password="pw", role=UserRole.USER)
        db.add(u1)
        db.commit()

        # Intentionally attempt to insert duplicate primary key (simulating conflicting constraint)
        u2 = User(id=user_id, email=f"dup_{user_id}@kalyan.ai", username=f"dup_{user_id}", hashed_password="pw", role=UserRole.USER)
        db.add(u2)
        try:
            db.commit()
            pytest.fail("Should have failed with IntegrityError")
        except Exception:
            db.rollback()

        # Session must recover immediately and allow subsequent clean queries
        recovered_user = db.query(User).filter(User.id == user_id).first()
        assert recovered_user is not None
        assert recovered_user.id == user_id
        print(f"\n[+] Database Recovery Verified: Clean transaction resumption after rollback")
    finally:
        db.close()


def test_failure_injection_malformed_json_payload():
    """Failure Mode 5: Malformed JSON webhook payload -> HTTP 400 rejection without process panic."""
    malformed_body = b'{"event": "payment.captured", "unclosed_json: true'
    
    # Generate signature for the raw malformed bytes
    sig = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        malformed_body,
        hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/v1/subscriptions/webhook",
        content=malformed_body,
        headers={
            "Content-Type": "application/json",
            "x-razorpay-signature": sig
        }
    )

    assert response.status_code == 400
    assert "Malformed JSON payload" in response.json()["detail"]
    print(f"\n[+] Malformed JSON Rejection Verified: HTTP {response.status_code}")


def test_failure_injection_signed_payment_webhook_replay():
    """
    Failure Mode 6: Payment Webhook Replay & Duplicate Attack Defense
    - Missing signature -> 401 Unauthorized
    - Forged signature -> 401 Unauthorized
    - Valid signature -> 200 OK & Subscription activated
    - Replay attack (identical payload + signature) -> 200 OK with 'idempotent replay skipped'
    - Verifies zero double-crediting
    """
    db = SessionLocal()
    user_tag = f"hook-{uuid.uuid4().hex[:6]}"
    user = User(id=f"user-{user_tag}", email=f"{user_tag}@kalyan.ai", username=f"u_{user_tag}", hashed_password="pw")
    db.add(user)
    db.commit()

    payment_id = f"pay_test_{uuid.uuid4().hex[:10]}"
    webhook_dict = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "amount": 14900,
                    "currency": "INR",
                    "status": "captured",
                    "notes": {
                        "user_id": user.id,
                        "plan_tier": "fan_pass_149"
                    }
                }
            }
        }
    }
    payload_bytes = json.dumps(webhook_dict).encode("utf-8")

    # 1. Missing signature
    resp_no_sig = client.post("/api/v1/subscriptions/webhook", content=payload_bytes, headers={"Content-Type": "application/json"})
    assert resp_no_sig.status_code == 401
    assert "Missing webhook signature" in resp_no_sig.json()["detail"]

    # 2. Forged signature
    resp_bad_sig = client.post(
        "/api/v1/subscriptions/webhook",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "x-razorpay-signature": "forged_invalid_signature_hex"}
    )
    assert resp_bad_sig.status_code == 401
    assert "Invalid webhook signature" in resp_bad_sig.json()["detail"]

    # 3. Legitimate signed delivery
    valid_sig = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    resp_valid = client.post(
        "/api/v1/subscriptions/webhook",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "x-razorpay-signature": valid_sig}
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json()["status"] == "ok"
    assert resp_valid.json()["message"] == "Payment verified and subscription activated"

    # Verify database state after initial delivery
    txn_count_initial = db.query(PaymentTransaction).filter(PaymentTransaction.payment_reference == payment_id).count()
    assert txn_count_initial == 1

    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    assert sub is not None
    assert sub.plan_tier == "fan_pass_149"
    initial_total_paid = sub.total_paid_inr

    # 4. REPLAY ATTACK: Submit identical webhook again
    resp_replay = client.post(
        "/api/v1/subscriptions/webhook",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "x-razorpay-signature": valid_sig}
    )
    assert resp_replay.status_code == 200
    assert "idempotent replay skipped" in resp_replay.json()["message"]

    # Assert zero double-crediting occurred
    db.refresh(sub)
    txn_count_after = db.query(PaymentTransaction).filter(PaymentTransaction.payment_reference == payment_id).count()
    assert txn_count_after == 1, "Duplicate payment transaction record was created!"
    assert sub.total_paid_inr == initial_total_paid, "User balance was double-credited on replay!"
    
    db.close()
    print(f"\n[+] Payment Replay Defense Verified: 100% Idempotent, zero double-crediting")
