"""
backend/scripts/test_social_publishing_pipeline.py
Automated verification script for Phase 6.3 Task 2:
Multi-platform Social Media Adapters & Outbox Publishing Pipeline.
"""

import sys
import os
import json
import uuid
from datetime import datetime, timezone
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.database import SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.content import ContentCandidate, PublishedAction
from backend.app.models.safety import AuditLog
from backend.app.services.social_gateway import (
    SocialPublisherService,
    SocialPublishError,
    XAdapter,
    InstagramAdapter,
    YouTubeAdapter,
    WhatsAppAdapter,
)
from backend.app.services.kill_switch import KillSwitchManager
from backend.app.services.content_engine import ContentEngine
from backend.app.core.config import settings


def run_social_publishing_verification():
    print("=================================================================")
    print("🚀 PHASE 6.3 TASK 2: SOCIAL MEDIA ADAPTERS & OUTBOX PIPELINE TEST")
    print("=================================================================\n")

    db = SessionLocal()
    kill_switch = KillSwitchManager(db)
    publisher = SocialPublisherService(db)
    content_engine = ContentEngine(db)

    # Ensure clean starting state for kill switch
    kill_switch.deactivate(actor_id="test_runner", reason="Pre-test reset")

    passed_checks = 0
    total_checks = 7

    # Ensure operator user exists in DB
    operator_user = db.query(User).filter(User.role == UserRole.OPERATOR).first()
    if not operator_user:
        operator_user = User(
            id=str(uuid.uuid4()),
            email="operator_pipeline@kalyan.ai",
            hashed_password="hashed_pw_test",
            role=UserRole.OPERATOR,
            is_active=True,
            is_verified=True,
        )
        db.add(operator_user)
        db.commit()

    # -------------------------------------------------------------
    # 1. Test All 4 Social Adapters in isolation
    # -------------------------------------------------------------
    print("[Check 1/7] Testing Individual Social Platform Adapters...")
    sample_text = "Sharma ji ka beta cracking FAANG won't pay your rent. Build your own skills, guru! #KalyanTruth"

    x_adapter = XAdapter()
    ig_adapter = InstagramAdapter()
    yt_adapter = YouTubeAdapter()
    wa_adapter = WhatsAppAdapter()

    x_res = x_adapter.publish(sample_text)
    ig_res = ig_adapter.publish(sample_text)
    yt_res = yt_adapter.publish(sample_text)
    wa_res = wa_adapter.publish(sample_text, payload={"recipient_phone": "+919876543210"})

    assert x_res["platform"] == "x" and "external_id" in x_res, "XAdapter failure"
    assert ig_res["platform"] == "instagram" and "external_id" in ig_res, "InstagramAdapter failure"
    assert yt_res["platform"] == "youtube" and "external_id" in yt_res, "YouTubeAdapter failure"
    assert wa_res["platform"] == "whatsapp" and wa_res["status"] == "sent", "WhatsAppAdapter failure"

    print(f"  ✓ X Adapter: ID={x_res['external_id']} (Mode={x_res['mode']})")
    print(f"  ✓ Instagram Adapter: ID={ig_res['external_id']} (Mode={ig_res['mode']})")
    print(f"  ✓ YouTube Adapter: ID={yt_res['external_id']} (Mode={yt_res['mode']})")
    print(f"  ✓ WhatsApp Adapter: ID={wa_res['external_id']} (Mode={wa_res['mode']})")
    passed_checks += 1

    # -------------------------------------------------------------
    # 2. Meta Webhook Verification Handshake (GET /webhook/meta)
    # -------------------------------------------------------------
    print("\n[Check 2/7] Testing Meta Webhook Verification Challenge...")
    from backend.app.api.v1.publisher import meta_webhook_verification
    from fastapi import HTTPException

    challenge = "challenge_token_abc123"
    verify_res = meta_webhook_verification(
        hub_mode="subscribe",
        hub_verify_token=settings.WHATSAPP_VERIFY_TOKEN,
        hub_challenge=challenge,
        db=db
    )
    assert verify_res.body.decode() == challenge, "Meta challenge verification failed"

    # Verify invalid token gets 403
    rejected = False
    try:
        meta_webhook_verification(
            hub_mode="subscribe",
            hub_verify_token="wrong_token",
            hub_challenge=challenge,
            db=db
        )
    except HTTPException as e:
        if e.status_code == 403:
            rejected = True
    assert rejected, "Invalid Meta verify token was not rejected with 403"
    print("  ✓ Meta Webhook Challenge Handshake & Security Rejection Verified.")
    passed_checks += 1

    # -------------------------------------------------------------
    # 3. Ingestion of Inbound Mentions via Webhook (POST /webhook/meta)
    # -------------------------------------------------------------
    print("\n[Check 3/7] Testing Inbound Social Mention Ingestion & Draft Creation...")
    from backend.app.api.v1.publisher import meta_webhook_event

    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "wa_acc_123",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "+919123456780",
                                    "id": "wamid.HBgLM...",
                                    "timestamp": "1710000000",
                                    "text": {"body": "Bro should I quit my TCS job for a startup offering 15 LPA?"},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    event_res = meta_webhook_event(meta_payload, db=db)
    assert event_res["status"] == "processed"
    assert event_res["ingested_count"] == 1
    ingested_cand_id = event_res["items"][0]["candidate_id"]
    print(f"  ✓ Webhook Ingested Message -> Created Candidate {ingested_cand_id}")
    print(f"    Draft Reply: {event_res['items'][0]['draft_reply']}")
    passed_checks += 1

    # -------------------------------------------------------------
    # 4. Human Approval Workflow (pending_approval -> approved)
    # -------------------------------------------------------------
    print("\n[Check 4/7] Testing Human Operator Review & Approval Workflow...")
    cand = db.query(ContentCandidate).filter(ContentCandidate.id == ingested_cand_id).first()
    assert cand is not None, "Ingested candidate not found in DB"
    
    # Ensure it's approved
    cand.status = "approved"
    cand.approved_by = operator_user.id
    cand.approved_at = datetime.now(timezone.utc)
    db.commit()

    # Direct publishing via publisher service
    publish_res = publisher.publish_candidate(candidate_id=cand.id, operator_id=operator_user.id)
    assert publish_res["success"] is True
    assert publish_res["status"] == "published"
    assert "external_id" in publish_res
    print(f"  ✓ Candidate Approved & Published Directly: ActionID={publish_res['published_action_id']}, ExternalID={publish_res['external_id']}")
    passed_checks += 1

    # -------------------------------------------------------------
    # 5. Outbox Pattern: Kill Switch Blocking Verification
    # -------------------------------------------------------------
    print("\n[Check 5/7] Testing Outbox Pattern Under Emergency Kill Switch...")
    # Create 3 queued candidates and outbox actions
    outbox_cand_ids = []
    for platform in ["x", "instagram", "youtube"]:
        c = ContentCandidate(
            id=str(uuid.uuid4()),
            source_channel=platform,
            pillar="career_realism",
            format="post",
            raw_prompt=f"Test kill switch for {platform}",
            candidate_text=f"Kill switch test post for {platform}",
            risk_tier="tier_1",
            status="approved",
            created_at=datetime.now(timezone.utc)
        )
        db.add(c)
        db.commit()
        outbox_cand_ids.append(c.id)

        action = PublishedAction(
            id=str(uuid.uuid4()),
            candidate_id=c.id,
            channel=platform,
            published_at=datetime.now(timezone.utc),
            status="queued"
        )
        db.add(action)
        db.commit()

    # Engage Kill Switch
    kill_switch.activate(actor_id=operator_user.id, reason="Testing Outbox Emergency Abort")
    assert kill_switch.is_kill_switch_active() is True, "Kill switch failed to engage"

    # Drain Outbox while Kill Switch is active
    drain_blocked_res = publisher.drain_outbox(max_batch=10)
    print(f"  Outbox Drain Result (Kill Switch ACTIVE): {drain_blocked_res}")
    assert drain_blocked_res["cancelled"] >= 3, "Outbox did not cancel queued items during kill switch"
    assert drain_blocked_res["published"] == 0, "Outbox published items despite kill switch active!"

    # Verify records in DB
    cancelled_actions = db.query(PublishedAction).filter(
        PublishedAction.status == "cancelled_by_kill_switch"
    ).all()
    assert len(cancelled_actions) >= 3, "Cancelled actions not updated in database"
    print(f"  ✓ Emergency Kill Switch safely blocked and cancelled {len(cancelled_actions)} outbound dispatches.")
    passed_checks += 1

    # -------------------------------------------------------------
    # 6. Outbox Pattern: Successful Drain when Disengaged
    # -------------------------------------------------------------
    print("\n[Check 6/7] Testing Outbox Pattern Normal Drain (Kill Switch DISENGAGED)...")
    # Disengage Kill Switch
    kill_switch.deactivate(actor_id=operator_user.id, reason="Normal ops resumed")
    assert kill_switch.is_kill_switch_active() is False, "Kill switch failed to disengage"

    # Queue fresh items for all channels
    fresh_channels = ["x", "instagram", "youtube", "whatsapp"]
    fresh_action_ids = []
    for ch in fresh_channels:
        c = ContentCandidate(
            id=str(uuid.uuid4()),
            source_channel=ch,
            pillar="salary_negotiation",
            format="reel" if ch in ["instagram", "youtube"] else "post",
            raw_prompt=f"Outbox dispatch for {ch}",
            candidate_text=f"Salary negotiation truth on {ch}: always ask for numbers in writing.",
            risk_tier="tier_0",
            status="approved",
            created_at=datetime.now(timezone.utc)
        )
        db.add(c)
        db.commit()

        action = PublishedAction(
            id=str(uuid.uuid4()),
            candidate_id=c.id,
            channel=ch,
            published_at=datetime.now(timezone.utc),
            status="queued"
        )
        db.add(action)
        db.commit()
        fresh_action_ids.append(action.id)

    drain_success_res = publisher.drain_outbox(max_batch=10)
    print(f"  Outbox Drain Result (Normal Ops): {drain_success_res}")
    assert drain_success_res["published"] >= 4, f"Expected >= 4 published, got {drain_success_res['published']}"
    assert drain_success_res["failed"] == 0, "Unexpected failures in outbox drain"

    # Verify each action is now 'success' with external_post_id
    for aid in fresh_action_ids:
        rec = db.query(PublishedAction).filter(PublishedAction.id == aid).first()
        assert rec.status == "success", f"Action {aid} status is {rec.status}"
        assert rec.external_post_id is not None, f"Action {aid} missing external_post_id"
    print(f"  ✓ All {len(fresh_action_ids)} queued social items dispatched cleanly via Outbox pattern.")
    passed_checks += 1

    # -------------------------------------------------------------
    # 7. Audit Log Integrity Check
    # -------------------------------------------------------------
    print("\n[Check 7/7] Verifying Audit Trail & Forensic Records...")
    recent_audits = (
        db.query(AuditLog)
        .filter(AuditLog.action.in_(["CONTENT_PUBLISHED", "KILL_SWITCH_ENGAGED", "KILL_SWITCH_DISENGAGED"]))
        .order_by(AuditLog.timestamp.desc())
        .limit(10)
        .all()
    )
    assert len(recent_audits) > 0, "No audit logs recorded for publishing/kill switch events"
    for audit in recent_audits[:4]:
        print(f"  ✓ Audit: Actor={audit.actor_id} | Action={audit.action} | Target={audit.target_id} | Time={audit.timestamp}")
    passed_checks += 1

    print("\n=================================================================")
    print(f"🎉 SOCIAL PUBLISHING PIPELINE VERIFICATION PASSED: {passed_checks}/{total_checks} CHECKS GREEN")
    print("=================================================================")
    db.close()
    return True


if __name__ == "__main__":
    success = run_social_publishing_verification()
    sys.exit(0 if success else 1)
