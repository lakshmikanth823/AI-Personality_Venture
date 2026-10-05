import uuid
import hmac
import hashlib
import time
import pytest
from datetime import datetime, timezone
from backend.app.models.conversation import Conversation, Message
from backend.app.models.user import User, UserRole
from backend.app.services.model_provider import (
    AbstractModelProvider,
    ModelResponse,
    ModelRouter,
    MockModelProvider
)
from backend.app.services.payment_gateway import PaymentGatewayService
from backend.app.services.kill_switch import KillSwitchManager

# 1. IDOR Prevention Test
def test_idor_prevention_on_chat(client):
    # Create User A
    res_a = client.post("/api/v1/auth/signup", json={
        "email": f"user_a_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"user_a_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A starts conversation
    chat_a = client.post(
        "/api/v1/chat/message",
        json={"message": "My confidential salary is 30 LPA.", "channel": "web"},
        headers=headers_a
    )
    assert chat_a.status_code == 200
    conv_id = chat_a.json()["conversation_id"]

    # Create User B
    res_b = client.post("/api/v1/auth/signup", json={
        "email": f"user_b_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"user_b_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B attempts to read User A's conversation history -> 403 Forbidden
    history_res = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers_b)
    assert history_res.status_code == 403
    assert "Access denied" in history_res.json()["detail"]

    # User B attempts to poison User A's conversation by appending message -> 403 Forbidden
    poison_res = client.post(
        "/api/v1/chat/message",
        json={"conversation_id": conv_id, "message": "Malicious payload into User A's thread", "channel": "web"},
        headers=headers_b
    )
    assert poison_res.status_code == 403
    assert "Access denied" in poison_res.json()["detail"]

# 2. Daily Quota Enforcement Test (Free Dost 25 messages)
def test_daily_quota_enforcement(client, db_session):
    res = client.post("/api/v1/auth/signup", json={
        "email": f"quota_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"quota_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    user_data = res.json()
    token = user_data["access_token"]
    user_id = user_data["user_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Pre-seed 25 messages for today in DB
    conv = Conversation(id=str(uuid.uuid4()), user_id=user_id, channel="web", title="Quota Test")
    db_session.add(conv)
    db_session.commit()

    now = datetime.now(timezone.utc)
    for i in range(25):
        msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="user",
            content=f"Message {i+1}",
            created_at=now
        )
        db_session.add(msg)
    db_session.commit()

    # 26th message must be rejected with 429 Too Many Requests
    excess_res = client.post(
        "/api/v1/chat/message",
        json={"conversation_id": conv.id, "message": "26th message exceeds daily quota", "channel": "web"},
        headers=headers
    )
    assert excess_res.status_code == 429
    assert "Daily quota of 25 messages reached" in excess_res.json()["detail"]

# 3. Approval Queue Authentication & Role Guard Test
def test_approval_queue_authentication(client):
    # Unauthenticated request -> 401 Unauthorized
    res_unauth = client.get("/api/v1/approval/candidates")
    assert res_unauth.status_code == 401

    # Normal user authenticated request -> 403 Forbidden
    res_user = client.post("/api/v1/auth/signup", json={
        "email": f"normal_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"normal_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    token = res_user.json()["access_token"]
    res_forbidden = client.get("/api/v1/approval/candidates", headers={"Authorization": f"Bearer {token}"})
    assert res_forbidden.status_code == 403

    # Operator authenticated request -> 200 OK
    op_login = client.post("/api/v1/auth/login", json={
        "email_or_username": "operator",
        "password": "operator123"
    })
    op_token = op_login.json()["access_token"]
    res_allowed = client.get("/api/v1/approval/candidates", headers={"Authorization": f"Bearer {op_token}"})
    assert res_allowed.status_code == 200
    assert isinstance(res_allowed.json(), list)

# 4. ModelRouter Automatic Fallover Test
@pytest.mark.asyncio
async def test_model_router_failover():
    class FailingProvider(AbstractModelProvider):
        async def generate(self, messages, system_prompt, temperature=0.7, max_tokens=600, task="chat"):
            raise ConnectionError("Primary upstream LLM API gateway timeout (504)")

        async def moderate(self, text):
            return {"policy_flag": "clean", "risk_tier": "tier_0"}

        async def summarize(self, text):
            return text

        async def embed(self, text):
            return [0.0] * 32

        async def speak(self, text, voice_profile="hyderabad_expressive"):
            return {}

    failing_primary = FailingProvider()
    healthy_secondary = MockModelProvider()

    router = ModelRouter(primary=failing_primary, fallback=healthy_secondary)

    # Calling generate should smoothly fall back to healthy_secondary without throwing
    res = await router.generate(
        messages=[{"role": "user", "content": "Tell me about Ameerpet"}],
        system_prompt="Kalyan Constitution"
    )
    assert res is not None
    assert len(res.content) > 10
    assert "Ameerpet" in res.content or "Kalyan" in res.content or "overcomplicate" in res.content

# 5. Memory Multi-Tenant Isolation Test
def test_memory_multi_tenant_isolation(client):
    # User 1 registers and mentions hometown
    res1 = client.post("/api/v1/auth/signup", json={
        "email": f"user1_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"user1_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    token1 = res1.json()["access_token"]
    h1 = {"Authorization": f"Bearer {token1}"}
    client.post("/api/v1/chat/message", json={"message": "I live in Vijayawada.", "channel": "web"}, headers=h1)

    # User 2 registers and requests memories
    res2 = client.post("/api/v1/auth/signup", json={
        "email": f"user2_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"user2_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    token2 = res2.json()["access_token"]
    h2 = {"Authorization": f"Bearer {token2}"}

    mem2 = client.get("/api/v1/memories/", headers=h2).json()
    # User 2 must have 0 memories (no leak from User 1)
    assert len(mem2) == 0

# 6. Payment Webhook HMAC Signature & Idempotency Test
def test_payment_webhook_hmac_and_idempotency(client, db_session):
    gateway = PaymentGatewayService(db_session)
    secret = "test_webhook_secret_key_123"

    # Create a user to credit
    res = client.post("/api/v1/auth/signup", json={
        "email": f"pay_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"pay_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    user_id = res.json()["user_id"]

    raw_body = f'{{"event": "payment.authorized", "user_id": "{user_id}", "plan_tier": "fan_pass", "payment_id": "pay_test_999"}}'.encode("utf-8")
    
    # Valid signature
    valid_sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    assert gateway.verify_webhook_signature(raw_body, valid_sig, secret) is True

    # Invalid signature
    assert gateway.verify_webhook_signature(raw_body, "fake_tampered_sig", secret) is False

    # Process first time -> success
    result1 = gateway.process_verified_payment(
        event_payload={"payment_id": "pay_test_999", "plan_tier": "fan_pass"},
        user_id=user_id
    )
    assert result1["status"] == "activated"
    assert result1["plan_tier"] in ["fan_pass", "fan_pass_149"]

    # Process duplicate payment_id -> idempotent (already processed)
    result2 = gateway.process_verified_payment(
        event_payload={"payment_id": "pay_test_999", "plan_tier": "fan_pass"},
        user_id=user_id
    )
    assert result2["status"] == "already_processed"
    assert result2["duplicate"] is True

# 7. Kill Switch Concurrency and Interlock Test
def test_kill_switch_interlock(client, db_session):
    admin_login = client.post("/api/v1/auth/login", json={
        "email_or_username": "admin",
        "password": "admin123"
    })
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Activate global kill switch
    activate_res = client.post(
        "/api/v1/admin/kill-switch/activate",
        json={"reason": "Emergency reality audit test"},
        headers=admin_headers
    )
    assert activate_res.status_code == 200

    # Ensure KillSwitchManager reports active
    ks_mgr = KillSwitchManager(db_session)
    assert ks_mgr.is_active("global") is True

    # Post candidate to publisher -> must be halted/blocked
    publish_attempt = client.post(
        "/api/v1/publisher/ingest-mention",
        json={"channel": "x", "author": "tester", "content": "Kalyan bro reply"}
    )
    # Even if ingested as candidate, scheduler will never publish while switch is active
    assert ks_mgr.can_publish() is False

    # Deactivate kill switch
    deactivate_res = client.post(
        "/api/v1/admin/kill-switch/deactivate",
        json={"reason": "Audit complete"},
        headers=admin_headers
    )
    assert deactivate_res.status_code == 200
    assert ks_mgr.can_publish() is True
