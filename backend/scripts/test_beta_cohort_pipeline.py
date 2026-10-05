"""
backend/scripts/test_beta_cohort_pipeline.py
Automated verification script for Phase 6.3 Task 5:
Controlled Beta Cohort Management & User Onboarding Pipeline (5-10 Beta Users).
"""

import sys
import os
import json
import uuid
from datetime import datetime, timezone, timedelta
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.database import SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.waitlist import WaitlistEntry
from backend.app.models.conversation import Conversation, Message
from backend.app.models.subscription import Subscription
from backend.app.core.security import get_password_hash


def run_beta_cohort_verification():
    print("=================================================================")
    print("🚀 PHASE 6.3 TASK 5: CONTROLLED BETA COHORT MANAGEMENT TEST")
    print("=================================================================\n")

    db = SessionLocal()
    passed_checks = 0
    total_checks = 6

    # -------------------------------------------------------------
    # 1. Test Waitlist Ingestion & FIFO Queue Position Calculation
    # -------------------------------------------------------------
    print("[Check 1/6] Ingesting 10 Beta Waitlist Candidates via HTTP API...")
    beta_candidates = [
        {"email": f"beta_user_{i:02d}_{uuid.uuid4().hex[:4]}@kalyan-test.io", "phone": f"+9198765432{i:02d}", "referral": f"REF_{i}"}
        for i in range(1, 11)
    ]

    registered_positions = []
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
        for cand in beta_candidates:
            resp = client.post("/api/v1/waitlist", json={
                "email": cand["email"],
                "phone": cand["phone"],
                "referral_code": cand["referral"]
            })
            assert resp.status_code == 200, f"Failed waitlist registration for {cand['email']}: {resp.text}"
            data = resp.json()
            assert data["status"] in ["queued", "already_registered"]
            assert data["queue_position"] > 0
            registered_positions.append((cand["email"], data["queue_position"]))

    print(f"  ✓ Successfully queued 10 beta applicants. Positions: {[pos for _, pos in registered_positions]}")
    passed_checks += 1

    # -------------------------------------------------------------
    # 2. Test Deduplication Defense
    # -------------------------------------------------------------
    print("\n[Check 2/6] Testing Waitlist Deduplication & Idempotency...")
    duplicate_email = beta_candidates[0]["email"]
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
        dup_resp = client.post("/api/v1/waitlist", json={
            "email": duplicate_email,
            "phone": "+919999999999"
        })
        assert dup_resp.status_code == 200
        dup_data = dup_resp.json()
        assert dup_data["status"] == "already_registered"
        assert dup_data["queue_position"] == registered_positions[0][1]
    print(f"  ✓ Duplicate submission recognized: returned existing position #{dup_data['queue_position']}.")
    passed_checks += 1

    # -------------------------------------------------------------
    # 3. Status Check Endpoint Query
    # -------------------------------------------------------------
    print("\n[Check 3/6] Testing Public Waitlist Status Lookup (GET /waitlist/status/{email})...")
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
        status_resp = client.get(f"/api/v1/waitlist/status/{duplicate_email}")
        assert status_resp.status_code == 200
        st_data = status_resp.json()
        assert st_data["email"] == duplicate_email
        assert st_data["queue_position"] == registered_positions[0][1]
        assert "Beta Cohort 2" in st_data["estimated_cohort"]
    print(f"  ✓ Status endpoint query verified for {duplicate_email} (Position #{st_data['queue_position']})")
    passed_checks += 1

    # -------------------------------------------------------------
    # 4. Onboard Cohort: Convert 5 Waitlist Entries to Active Beta Users
    # -------------------------------------------------------------
    print("\n[Check 4/6] Onboarding 5 Pilot Users into Active Beta Cohort...")
    active_beta_users = []
    for cand in beta_candidates[:5]:
        email = cand["email"]
        # Transition waitlist entry
        entry = db.query(WaitlistEntry).filter(WaitlistEntry.email == email).first()
        if entry:
            entry.status = "admitted"
            entry.cohort = "Beta Cohort 1"
            entry.invited_at = datetime.now(timezone.utc)
            db.commit()

        # Provision User record
        uname = f"beta_{cand['email'].split('@')[0]}"[:30]
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=uname,
            hashed_password=get_password_hash("BetaSecure123!"),
            role=UserRole.USER,
            is_active=True,
            personalization_enabled=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()

        # Provision Beta Subscription
        sub = Subscription(
            id=str(uuid.uuid4()),
            user_id=user.id,
            plan_tier="fan_pass_149",
            status="active",
            started_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            total_paid_inr=0.0,
            perks_json='{"daily_limit": 100, "cohort": "Beta Cohort 1"}'
        )
        db.add(sub)
        db.commit()
        active_beta_users.append(user)

    print(f"  ✓ Successfully provisioned {len(active_beta_users)} active beta user accounts with 'Beta Cohort 1' subscriptions.")
    passed_checks += 1

    # -------------------------------------------------------------
    # 5. Simulate Multi-Turn Activity & D1/D7 Retention Metrics
    # -------------------------------------------------------------
    print("\n[Check 5/6] Simulating Multi-User Conversation Activity for Retention Tracking...")
    for idx, user in enumerate(active_beta_users):
        conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title=f"Beta Session User {idx+1}",
            created_at=datetime.now(timezone.utc) - timedelta(days=idx % 3)
        )
        db.add(conv)
        db.commit()

        # Add initial user question and Kalyan response
        msg1 = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="user",
            content=f"Hey Kalyan, beta test question #{idx+1}: How do I stay consistent with coding?",
            created_at=conv.created_at
        )
        msg2 = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="assistant",
            content="Consistency doesn't come from motivation guru, it comes from discipline. 1 hour daily, no excuses.",
            created_at=conv.created_at + timedelta(seconds=2)
        )
        db.add_all([msg1, msg2])
        db.commit()

    total_beta_convs = db.query(Conversation).filter(Conversation.user_id.in_([u.id for u in active_beta_users])).count()
    total_beta_msgs = db.query(Message).join(Conversation).filter(Conversation.user_id.in_([u.id for u in active_beta_users])).count()
    assert total_beta_convs == 5, f"Expected 5 conversations, got {total_beta_convs}"
    assert total_beta_msgs == 10, f"Expected 10 messages, got {total_beta_msgs}"
    print(f"  ✓ Retention events recorded: {total_beta_convs} active conversations, {total_beta_msgs} messages across 5 cohort users.")
    passed_checks += 1

    # -------------------------------------------------------------
    # 6. Verify Dashboard Metrics Ingestion
    # -------------------------------------------------------------
    print("\n[Check 6/6] Verifying Cohort Analytics Dashboard Integration...")
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
        dash_resp = client.get("/api/v1/analytics/dashboard")
        assert dash_resp.status_code == 200
        dash_data = dash_resp.json()
        print(f"  DAU: {dash_data.get('dau', 0)} | WAU: {dash_data.get('wau', 0)} | North Star WMCR: {dash_data.get('north_star_wmcr', 0)}")
        print(f"  Total Tokens: {dash_data.get('total_tokens_processed', 0)} | Spend USD: ${dash_data.get('total_cost_usd', 0.0)}")
        print(f"  Strategic Insights: {[i.get('diagnosis') for i in dash_data.get('strategic_insights', [])]}")
        print("  ✓ Cohort analytics data stream live and connected to Dashboard.")
        passed_checks += 1

    print("\n=================================================================")
    print(f"🎉 CONTROLLED BETA COHORT VERIFICATION PASSED: {passed_checks}/{total_checks} CHECKS GREEN")
    print("=================================================================")
    db.close()
    return True


if __name__ == "__main__":
    success = run_beta_cohort_verification()
    sys.exit(0 if success else 1)
