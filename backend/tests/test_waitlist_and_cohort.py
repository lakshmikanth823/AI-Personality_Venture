"""
Waitlist & Cohort Capacity Test Suite (Phase 4 Section 1.3)
Verifies:
1. Waitlist persistence and FIFO queue position allocation.
2. Waitlist deduplication.
3. Cohort cap enforcement at signup (N=50 on SQLite) with waitlist overflow prompt.
4. Admin/Operator bypass for capacity check.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.waitlist import WaitlistEntry

client = TestClient(app)

def test_waitlist_registration_and_queue_position():
    """Verify waitlist submission and FIFO queue progression."""
    tag = uuid.uuid4().hex[:6]
    email1 = f"waiter1_{tag}@kalyan.ai"
    email2 = f"waiter2_{tag}@kalyan.ai"

    # User 1 joins waitlist
    r1 = client.post("/api/v1/waitlist", json={"email": email1, "phone": "+919876543210"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["status"] == "queued"
    pos1 = d1["queue_position"]

    # User 2 joins waitlist
    r2 = client.post("/api/v1/waitlist", json={"email": email2})
    assert r2.status_code == 200
    d2 = r2.json()
    pos2 = d2["queue_position"]
    assert pos2 == pos1 + 1, "Queue position must strictly increment FIFO"

    # Deduplication check: User 1 rejoins
    r1_dup = client.post("/api/v1/waitlist", json={"email": email1})
    assert r1_dup.status_code == 200
    assert r1_dup.json()["status"] == "already_registered"
    assert r1_dup.json()["queue_position"] == pos1

    # Status lookup
    r_status = client.get(f"/api/v1/waitlist/status/{email1}")
    assert r_status.status_code == 200
    assert r_status.json()["queue_position"] == pos1

def test_beta_cohort_cap_enforcement_at_signup(monkeypatch):
    """Verify that when beta cohort capacity is reached, signups are blocked and directed to waitlist."""
    db = SessionLocal()
    # Temporarily set BETA_COHORT_CAP to existing user count to simulate full capacity
    current_count = db.query(User).filter(User.is_active == True, User.role == UserRole.USER).count()
    db.close()

    monkeypatch.setattr(settings, "BETA_COHORT_CAP", current_count)
    monkeypatch.setattr(settings, "APP_ENV", "staging")  # enable capacity enforcement (bypassed in "test" env)

    tag = uuid.uuid4().hex[:6]
    # Normal user signup should be rejected with 403 Forbidden
    resp = client.post("/api/v1/auth/signup", json={
        "email": f"overflow_{tag}@kalyan.ai",
        "username": f"overflow_{tag}",
        "password": "Password123!",
        "consent_given": True
    })
    assert resp.status_code == 403
    assert "Beta cohort is at capacity" in resp.json()["detail"]
    assert "/api/v1/waitlist" in resp.json()["detail"]

    # Admin/Operator signup should still be allowed to onboard staff
    resp_admin = client.post("/api/v1/auth/signup", json={
        "email": f"staff_{tag}@kalyan.ai",
        "username": f"operator_{tag}",
        "password": "Password123!",
        "consent_given": True
    })
    # Since username starts with operator, it gets operator role and bypasses cap
    assert resp_admin.status_code == 200
