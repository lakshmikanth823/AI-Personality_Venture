import uuid
import time
import pyotp
import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.user import User, Profile, UserRole
from backend.app.models.memory import Memory
from backend.app.models.conversation import Conversation, Message
from backend.app.models.analytics import CostEvent
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.core.rate_limiter import limiter, SlidingWindowRateLimiter, get_client_ip
from backend.app.core.logging import scrub_sensitive_data
from backend.app.core.config import settings
from fastapi import Request

def test_mfa_setup_and_verification_flow(client):
    # 1. Signup normal user
    unique_email = f"mfa_{uuid.uuid4().hex[:6]}@kalyan-test.in"
    res = client.post("/api/v1/auth/signup", json={
        "email": unique_email,
        "username": f"mfa_{uuid.uuid4().hex[:6]}",
        "password": "StrongPassword123!"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check initial MFA status
    res_status = client.get("/api/v1/auth/mfa/status", headers=headers)
    assert res_status.status_code == 200
    assert res_status.json()["mfa_enabled"] is False

    # 3. Request MFA setup
    res_setup = client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert res_setup.status_code == 200
    setup_data = res_setup.json()
    secret = setup_data["secret"]
    assert "otpauth://" in setup_data["otpauth_url"]
    assert len(secret) >= 16

    # 4. Verify with wrong code -> 400 Bad Request
    res_fail = client.post("/api/v1/auth/mfa/verify", json={"code": "000000"}, headers=headers)
    assert res_fail.status_code == 400

    # 5. Verify with valid TOTP code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    res_verify = client.post("/api/v1/auth/mfa/verify", json={"code": valid_code}, headers=headers)
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["mfa_authenticated"] is True

    # 6. Verify MFA status is now True
    res_status_after = client.get("/api/v1/auth/mfa/status", headers={"Authorization": f"Bearer {verify_data['access_token']}"})
    assert res_status_after.status_code == 200
    assert res_status_after.json()["mfa_enabled"] is True

def test_mfa_enforcement_on_operator_and_admin_actions(client, db_session):
    # Create operator with MFA enabled
    secret = pyotp.random_base32()
    op_user = User(
        id=f"op-mfa-{uuid.uuid4().hex[:6]}",
        email=f"op_{uuid.uuid4().hex[:6]}@kalyan-test.in",
        username=f"op_{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("OperatorPass123!"),
        role=UserRole.OPERATOR,
        is_active=True,
        mfa_enabled=True,
        mfa_secret=secret
    )
    db_session.add(op_user)
    db_session.commit()

    # Step 1: Login with password only (no TOTP code supplied)
    login_res = client.post("/api/v1/auth/login", json={
        "email_or_username": op_user.username,
        "password": "OperatorPass123!"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["mfa_required"] is True
    assert login_data["mfa_authenticated"] is False
    partial_token = login_data["access_token"]
    partial_headers = {"Authorization": f"Bearer {partial_token}"}

    # Step 2: Attempting privileged operational action without MFA verification -> MUST BE 403 Forbidden!
    approval_res = client.get("/api/v1/approval/candidates", headers=partial_headers)
    assert approval_res.status_code == 403
    assert "MFA authentication required" in approval_res.json()["detail"]

    # Step 3: Complete TOTP verification
    totp = pyotp.TOTP(secret)
    verify_res = client.post("/api/v1/auth/mfa/verify", json={"code": totp.now()}, headers=partial_headers)
    assert verify_res.status_code == 200
    full_token = verify_res.json()["access_token"]
    full_headers = {"Authorization": f"Bearer {full_token}"}

    # Step 4: Now privileged action succeeds!
    approval_res_ok = client.get("/api/v1/approval/candidates", headers=full_headers)
    assert approval_res_ok.status_code == 200

def test_comprehensive_idor_matrix(client, db_session):
    # Setup User A and User B
    res_a = client.post("/api/v1/auth/signup", json={
        "email": f"userA_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"userA_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    user_a = res_a.json()
    headers_a = {"Authorization": f"Bearer {user_a['access_token']}"}

    res_b = client.post("/api/v1/auth/signup", json={
        "email": f"userB_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"userB_{uuid.uuid4().hex[:6]}",
        "password": "Password123!"
    })
    user_b = res_b.json()
    headers_b = {"Authorization": f"Bearer {user_b['access_token']}"}

    # 1. Create a conversation owned by User A
    chat_a = client.post("/api/v1/chat/message", json={
        "message": "User A secret Ameerpet plan",
        "channel": "web"
    }, headers=headers_a).json()
    conv_id_a = chat_a["conversation_id"]

    # 2. IDOR: User B attempts to read User A's conversation history -> 403 Forbidden
    history_res = client.get(f"/api/v1/chat/conversations/{conv_id_a}", headers=headers_b)
    assert history_res.status_code == 403
    assert "Access denied" in history_res.json()["detail"]

    # 3. IDOR: User B attempts to append message to User A's conversation -> 403 Forbidden
    append_res = client.post("/api/v1/chat/message", json={
        "conversation_id": conv_id_a,
        "message": "Malicious intrusion from User B",
        "channel": "web"
    }, headers=headers_b)
    assert append_res.status_code == 403
    assert "Access denied" in append_res.json()["detail"]

    # 4. IDOR: Memory deletion isolation
    mem_a = Memory(
        id=f"mem-a-{uuid.uuid4().hex[:6]}",
        user_id=user_a["user_id"],
        memory_type="l3_durable_fact",
        key="dream_job",
        value="Software Engineer in HITEC City",
        confidence=0.95
    )
    db_session.add(mem_a)
    db_session.commit()

    # User B attempts to delete User A's memory -> 404 (memory not found for user B)
    del_res = client.delete(f"/api/v1/memories/{mem_a.id}", headers=headers_b)
    assert del_res.status_code == 404

    # 5. Role Escalation IDOR: Normal User A cannot access Admin / Kill Switch
    admin_res = client.post("/api/v1/admin/kill-switch/activate", json={"reason": "Attacker shutdown"}, headers=headers_a)
    assert admin_res.status_code == 403

    # Normal User A cannot access Approval Queue
    appr_res = client.get("/api/v1/approval/candidates", headers=headers_a)
    assert appr_res.status_code == 403

def test_rate_limiter_sliding_window_and_spoof_defense():
    # Unit verification of SlidingWindowRateLimiter
    rl = SlidingWindowRateLimiter(default_limit=5, window_seconds=60)
    client_ip = "192.0.2.42"

    for i in range(5):
        assert rl.is_allowed(client_ip) is True
    # 6th request within window is blocked
    assert rl.is_allowed(client_ip) is False

    # Spoofed X-Forwarded-For Defense:
    # When behind_trusted_proxy is False, get_client_ip ignores untrusted X-Forwarded-For header
    class MockClient:
        host = "198.51.100.5"
    class MockRequest:
        client = MockClient()
        headers = {"x-forwarded-for": "203.0.113.195, 10.0.0.1"}

    untrusted_ip = get_client_ip(MockRequest(), behind_trusted_proxy=False)
    assert untrusted_ip == "198.51.100.5", "Must ignore spoofed X-Forwarded-For header when not configured"

    trusted_ip = get_client_ip(MockRequest(), behind_trusted_proxy=True)
    assert trusted_ip == "203.0.113.195", "Extracts correct origin IP when behind trusted reverse proxy"

def test_jwt_expired_token_and_invalid_signature(client):
    # Expired token (-1 hour)
    expired_token = create_access_token(
        data={"sub": "test-user-id", "role": "user"},
        expires_delta=timedelta(hours=-1)
    )
    res_exp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_exp.status_code == 401
    assert "Invalid or expired access token" in res_exp.json()["detail"]

    # Invalid secret signed token
    from jose import jwt
    bogus_token = jwt.encode({"sub": "test-user-id", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "wrong-secret-key-12345", algorithm="HS256")
    res_bogus = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bogus_token}"})
    assert res_bogus.status_code == 401

def test_must_change_password_workflow(client, db_session):
    temp_pass = "InitialTempPass123!"
    u = User(
        id=f"must-change-{uuid.uuid4().hex[:6]}",
        email=f"temp_{uuid.uuid4().hex[:6]}@kalyan-test.in",
        username=f"temp_{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash(temp_pass),
        role=UserRole.USER,
        is_active=True,
        must_change_password=True
    )
    db_session.add(u)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", json={
        "email_or_username": u.username,
        "password": temp_pass
    })
    assert login_res.status_code == 200
    assert login_res.json()["must_change_password"] is True
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change password
    new_pass = "NewBrandNewPassword2026!"
    change_res = client.post("/api/v1/auth/change-password", json={
        "current_password": temp_pass,
        "new_password": new_pass
    }, headers=headers)
    assert change_res.status_code == 200

    # Verify must_change_password is now False
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["must_change_password"] is False

def test_prometheus_metrics_endpoint(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers["content-type"]
    text = res.text
    assert "http_requests_total" in text
    assert "llm_tokens_total" in text
    assert "estimated_cost_usd_total" in text
    assert "content_approval_queue_depth" in text
    assert "kill_switch_active" in text

def test_pii_log_scrubbing():
    sample_log = "User test.kalyan@gmail.com with phone +919876543210 attempted login with password='SuperSecretPassword123' and api_key='sk-proj-1234567890abcdef'."
    scrubbed = scrub_sensitive_data(sample_log)
    assert "test.kalyan@gmail.com" not in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "+919876543210" not in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed
    assert "SuperSecretPassword123" not in scrubbed
    assert "[REDACTED_SECRET]" in scrubbed

def test_daily_cost_budget_ceiling(client, db_session):
    # Save original budget
    orig_budget = settings.DAILY_COST_BUDGET_USD
    try:
        # Set low budget for test
        settings.DAILY_COST_BUDGET_USD = 1.00

        # Inject cost event exceeding budget
        cost = CostEvent(
            id=f"cost-exceed-{uuid.uuid4().hex[:6]}",
            category="inference",
            amount_usd=1.50,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(cost)
        db_session.commit()

        # Chat message should be rejected with 429
        res = client.post("/api/v1/chat/message", json={
            "message": "Hello Kalyan, give me an expensive response",
            "channel": "web"
        })
        assert res.status_code == 429
        assert "Daily system inference budget cap" in res.json()["detail"]
    finally:
        settings.DAILY_COST_BUDGET_USD = orig_budget
        try:
            db_session.query(CostEvent).delete()
            db_session.commit()
        except Exception:
            db_session.rollback()
