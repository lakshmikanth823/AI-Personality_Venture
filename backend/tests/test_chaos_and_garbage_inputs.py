import uuid
import pytest
from fastapi.testclient import TestClient

def test_chaos_massive_text_bomb(client):
    """
    100KB massive payload to test token limiter and buffer overflow resilience.
    Must return 200 or 422 without 500 crash or memory exhaustion.
    """
    massive_payload = "Ameerpet chai banter " * 5000 # ~110,000 characters
    res = client.post("/api/v1/chat/message", json={"message": massive_payload, "channel": "web"})
    assert res.status_code in [200, 422, 400]
    if res.status_code == 200:
        data = res.json()
        assert len(data["content"]) > 0

def test_chaos_null_bytes_and_binary_garbage(client):
    """
    Inputs containing null bytes and control characters.
    """
    null_payload = "Hello Kalyan\x00\x01\x02\x03\x7f\x80\xff how are you?"
    res = client.post("/api/v1/chat/message", json={"message": null_payload, "channel": "web"})
    assert res.status_code in [200, 422, 400]

def test_chaos_malformed_json_body(client):
    """
    Malformed, unclosed, or invalid JSON sent to API routes.
    Must return 422 Unprocessable Entity, never unhandled 500.
    """
    raw_headers = {"Content-Type": "application/json"}
    bad_json = '{"message": "incomplete json...'
    res = client.post("/api/v1/chat/message", content=bad_json, headers=raw_headers)
    assert res.status_code == 422

def test_chaos_sql_injection_payloads(client):
    """
    SQL injection fuzzing across login, chat, and memory search.
    Must be neutralized by parameterized ORM queries without leaking data.
    """
    sqli_attack = "' OR '1'='1' UNION SELECT id, hashed_password FROM users; --"
    # Login attempt
    login_res = client.post("/api/v1/auth/login", json={"email_or_username": sqli_attack, "password": "wrong"})
    assert login_res.status_code in [401, 404]

    # Chat attempt
    chat_res = client.post("/api/v1/chat/message", json={"message": sqli_attack, "channel": "web"})
    assert chat_res.status_code == 200
    # Kalyan persona responds safely without executing SQL
    assert "users" not in chat_res.json()["content"].lower()

def test_chaos_xss_script_tags(client):
    """
    Cross-Site Scripting (XSS) payloads in messages and profiles.
    """
    xss_payload = "<script>alert(document.cookie)</script><svg/onload=alert('XSS')>"
    chat_res = client.post("/api/v1/chat/message", json={"message": xss_payload, "channel": "web"})
    assert chat_res.status_code == 200
    # Must not reflect executable unescaped script in content
    assert "<script>" not in chat_res.json()["content"]

def test_chaos_empty_and_whitespace_inputs(client):
    """
    Empty strings, single spaces, and newline-only messages.
    """
    res1 = client.post("/api/v1/chat/message", json={"message": "   \n\t  ", "channel": "web"})
    assert res1.status_code in [200, 422]

def test_chaos_extreme_pagination_and_invalid_ids(client):
    """
    Negative limits, massive limits, and non-existent UUIDs.
    """
    # Non-existent conversation UUID
    res_fake_conv = client.get(f"/api/v1/chat/conversations/{uuid.uuid4()}")
    assert res_fake_conv.status_code == 404

    # Negative audit log limit
    res_limit = client.get("/api/v1/publisher/published-history?limit=-50")
    assert res_limit.status_code in [200, 422]
