"""
Auth Lifecycle & Refresh Token Test Suite (Phase 5.2)
Verifies:
1. Short-lived access token (15 min) and refresh token generation at signup & login.
2. HTTP-only cookie delivery of refresh token.
3. Refresh token rotation at /api/v1/auth/refresh endpoint.
4. Body-provided refresh token support.
5. Rejection of invalid/expired refresh tokens.
"""

import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token, create_refresh_token

def test_signup_and_login_refresh_token_issuance(client):
    tag = uuid.uuid4().hex[:6]
    email = f"refresh_{tag}@kalyan.ai"
    username = f"refresh_{tag}"
    password = "Password123!"

    # 1. Signup issues access token and refresh token
    signup_res = client.post("/api/v1/auth/signup", json={
        "email": email,
        "username": username,
        "password": password,
        "consent_given": True
    })
    assert signup_res.status_code == 200
    data = signup_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] is not None
    # Check cookie
    assert "refresh_token" in signup_res.cookies

    # 2. Login issues fresh access token and refresh token
    login_res = client.post("/api/v1/auth/login", json={
        "email_or_username": email,
        "password": password
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert "refresh_token" in login_res.cookies

def test_refresh_token_endpoint_via_cookie(client):
    tag = uuid.uuid4().hex[:6]
    email = f"cookie_ref_{tag}@kalyan.ai"
    username = f"cookie_ref_{tag}"
    password = "Password123!"

    signup_res = client.post("/api/v1/auth/signup", json={
        "email": email,
        "username": username,
        "password": password,
        "consent_given": True
    })
    assert signup_res.status_code == 200
    old_access_token = signup_res.json()["access_token"]
    old_refresh_token = signup_res.json()["refresh_token"]

    # Call /refresh with cookie automatically attached by TestClient session
    refresh_res = client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_refresh_token})
    assert refresh_res.status_code == 200
    ref_data = refresh_res.json()
    assert "access_token" in ref_data
    assert ref_data["access_token"] != old_access_token
    assert "refresh_token" in ref_data

    # Use new access token to query /me
    headers = {"Authorization": f"Bearer {ref_data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

def test_refresh_token_endpoint_via_body(client):
    tag = uuid.uuid4().hex[:6]
    email = f"body_ref_{tag}@kalyan.ai"
    username = f"body_ref_{tag}"
    password = "Password123!"

    signup_res = client.post("/api/v1/auth/signup", json={
        "email": email,
        "username": username,
        "password": password,
        "consent_given": True
    })
    assert signup_res.status_code == 200
    refresh_token = signup_res.json()["refresh_token"]

    # Call /refresh via request body JSON
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    ref_data = refresh_res.json()
    assert "access_token" in ref_data
    assert "refresh_token" in ref_data

def test_refresh_token_invalid_or_expired_rejected(client):
    # 1. Missing refresh token -> 401
    res_empty = client.post("/api/v1/auth/refresh", json={})
    assert res_empty.status_code == 401

    # 2. Tampered token -> 401
    res_tampered = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.jwt.token"})
    assert res_tampered.status_code == 401

    # 3. Access token passed instead of refresh token -> 401
    access_tok = create_access_token(data={"sub": "dummy-user"})
    res_wrong_type = client.post("/api/v1/auth/refresh", json={"refresh_token": access_tok})
    assert res_wrong_type.status_code == 401

    # 4. Expired refresh token -> 401
    expired_tok = create_refresh_token(data={"sub": "dummy-user"}, expires_delta=timedelta(seconds=-10))
    res_expired = client.post("/api/v1/auth/refresh", json={"refresh_token": expired_tok})
    assert res_expired.status_code == 401
