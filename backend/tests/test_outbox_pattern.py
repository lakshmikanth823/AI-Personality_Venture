import uuid
import pytest
from backend.app.models.content import ContentCandidate, Approval, PublishedAction
from backend.app.services.content_engine import ContentEngine
from backend.app.services.social_gateway import SocialPublisherService
from backend.app.services.kill_switch import KillSwitchManager

def test_outbox_pattern_transactional_durability(db_session):
    # 1. Create a draft candidate
    cand = ContentCandidate(
        id=f"cand-{uuid.uuid4().hex[:6]}",
        source_channel="x",
        pillar="college_job",
        format="observation",
        raw_prompt="Ameerpet job market",
        candidate_text="Ameerpet Java institute certificates have higher liquidity than pre-IPO stock options.",
        risk_tier="tier_1",
        status="pending_approval"
    )
    db_session.add(cand)
    db_session.commit()

    engine = ContentEngine(db_session)
    res = engine.approve_and_queue(cand.id, operator_id="operator-123")
    assert res["status"] == "approved"
    assert "outbox_id" in res

    # Verify atomic writes in same transaction:
    # (a) Approval record created
    appr = db_session.query(Approval).filter(Approval.candidate_id == cand.id).first()
    assert appr is not None
    assert appr.operator_id == "operator-123"
    assert appr.action == "approved"

    # (b) PublishedAction outbox record enqueued with status="queued"
    outbox = db_session.query(PublishedAction).filter(PublishedAction.candidate_id == cand.id).first()
    assert outbox is not None
    assert outbox.status == "queued"
    assert outbox.channel == "x"

    # 2. Concurrency check: duplicate approval attempt MUST fail
    with pytest.raises(ValueError, match="already been approved or published"):
        engine.approve_and_queue(cand.id, operator_id="operator-456")

    # 3. Drain Outbox via SocialPublisherService
    publisher = SocialPublisherService(db_session)
    drain_res = publisher.drain_outbox(max_batch=10)
    assert drain_res["published"] == 1

    # Verify transition
    db_session.refresh(outbox)
    db_session.refresh(cand)
    assert outbox.status == "success"
    assert outbox.external_post_id is not None
    assert cand.status == "published"

def test_outbox_kill_switch_cancellation(db_session):
    # 1. Create approved candidate in outbox
    cand = ContentCandidate(
        id=f"cand-ks-{uuid.uuid4().hex[:6]}",
        source_channel="instagram",
        pillar="indian_internet_life",
        format="observation",
        raw_prompt="Instagram influencers",
        candidate_text="Influencers doing 'humble' charity videos with 4 4K cameras and a drone.",
        risk_tier="tier_1",
        status="approved"
    )
    db_session.add(cand)
    outbox = PublishedAction(
        id=f"outbox-{cand.id}",
        candidate_id=cand.id,
        channel="instagram",
        status="queued"
    )
    db_session.add(outbox)
    db_session.commit()

    # 2. Activate Emergency Kill Switch
    ks_mgr = KillSwitchManager(db_session)
    ks_mgr.activate(actor_id="admin-security", reason="Outbox safety drill")

    # 3. Drain Outbox: Worker must refuse broadcast and cancel queued action
    publisher = SocialPublisherService(db_session)
    drain_res = publisher.drain_outbox(max_batch=10)
    assert drain_res["cancelled"] == 1
    assert drain_res["published"] == 0

    db_session.refresh(outbox)
    assert outbox.status == "cancelled_by_kill_switch"

    # Clean up kill switch
    ks_mgr.deactivate(actor_id="admin-security", reason="Drill completed")
