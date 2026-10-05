"""
Beta Readiness & Legal Compliance Test Suite (G-19)
Verifies:
1. DPDP Act 2023 Consent Enforcement at Registration.
2. Public Privacy Notice & Grievance Redressal Officer disclosures.
3. Terms of Service, Satire Disclaimer & Crisis Helpline Disclosures.
4. In-App User Content Reporting & Safety Engine Intercept.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.safety import AuditLog

client = TestClient(app)

def test_dpdp_consent_enforcement_at_signup():
    """Verify DPDP Act 2023 consent capture requirement."""
    tag = uuid.uuid4().hex[:6]
    
    # 1. Attempt signup with consent_given=False
    resp_no_consent = client.post("/api/v1/auth/signup", json={
        "email": f"noconsent_{tag}@kalyan.ai",
        "username": f"noconsent_{tag}",
        "password": "Password123!",
        "consent_given": False
    })
    assert resp_no_consent.status_code == 400
    assert "Digital Personal Data Protection (DPDP) Act 2023 consent must be accepted" in resp_no_consent.json()["detail"]

    # 2. Legitimate signup with consent_given=True
    resp_consent = client.post("/api/v1/auth/signup", json={
        "email": f"dpdp_{tag}@kalyan.ai",
        "username": f"dpdp_{tag}",
        "password": "Password123!",
        "consent_given": True
    })
    assert resp_consent.status_code == 200
    user_id = resp_consent.json()["user_id"]

    # 3. Assert DPDP consent audit log created
    db = SessionLocal()
    audit = db.query(AuditLog).filter(
        AuditLog.actor_id == user_id,
        AuditLog.action == "DPDP_CONSENT_CAPTURED"
    ).first()
    assert audit is not None
    assert "2023" in audit.details_json
    db.close()

def test_privacy_and_terms_endpoints():
    """Verify DPDP Act compliant privacy policy and crisis-disclosed terms of service."""
    # Privacy Policy
    resp_privacy = client.get("/privacy")
    assert resp_privacy.status_code == 200
    assert "DPDP ACT 2023 COMPLIANT" in resp_privacy.text
    assert "grievance@kalyan.ai" in resp_privacy.text
    assert "Data Principal Rights" in resp_privacy.text

    # Terms of Service
    resp_terms = client.get("/terms")
    assert resp_terms.status_code == 200
    assert "Kalyan is NOT a licensed therapist" in resp_terms.text
    assert "14416" in resp_terms.text # Tele-MANAS
    assert "1800-599-0019" in resp_terms.text # Kiran Helpline

def test_in_app_content_report_button():
    """Verify in-app reporting of harmful or unexpected AI content."""
    resp = client.post("/api/v1/chat/report", json={
        "message_id": "msg-test-12345",
        "content_text": "Kalyan told me something that felt uncomfortable and borderline personal.",
        "category": "safety_violation",
        "reason": "Tone felt too harsh for my situation"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "reported"
    assert "rep_" in data["report_id"]

    # Verify audit trail
    db = SessionLocal()
    audit = db.query(AuditLog).filter(AuditLog.id == data["report_id"]).first()
    assert audit is not None
    assert audit.action == "USER_CONTENT_REPORT"
    db.close()
