import pytest
import uuid
from datetime import datetime, timezone
from backend.app.services.kill_switch import KillSwitchManager
from backend.app.services.social_gateway import SocialPublisherService, SocialPublishError
from backend.app.models.content import ContentCandidate

def test_kill_switch_lifecycle_and_interlock(db_session):
    mgr = KillSwitchManager(db_session)
    publisher = SocialPublisherService(db_session)

    # 1. Initially Kill Switch is OFF
    assert mgr.is_kill_switch_active() is False

    # Create candidate
    candidate = ContentCandidate(
        id=str(uuid.uuid4()),
        source_channel="x",
        pillar="college_job",
        format="observation",
        raw_prompt="test",
        candidate_text="Testing publishing workflow before emergency stop.",
        risk_tier="tier_0",
        status="approved",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(candidate)
    db_session.commit()

    # Publish succeeds when kill switch is OFF
    res = publisher.publish_candidate(candidate.id, operator_id="admin_1")
    assert res["status"] == "published"
    assert res["channel"] == "x"

    # 2. ENGAGE KILL SWITCH
    activation = mgr.activate(actor_id="admin_1", reason="Unusual autonomous anomaly reported")
    assert activation["is_active"] is True
    assert mgr.is_kill_switch_active() is True

    # 3. Create another approved candidate and attempt to publish
    candidate_2 = ContentCandidate(
        id=str(uuid.uuid4()),
        source_channel="x",
        pillar="college_job",
        format="observation",
        raw_prompt="test 2",
        candidate_text="This post should NEVER be published while kill switch is active.",
        risk_tier="tier_0",
        status="approved",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(candidate_2)
    db_session.commit()

    with pytest.raises(SocialPublishError, match="Emergency Kill Switch is currently ACTIVE"):
        publisher.publish_candidate(candidate_2.id, operator_id="admin_1")

    # 4. DISENGAGE KILL SWITCH & RESTORE
    deactivation = mgr.deactivate(actor_id="admin_1", reason="Incident resolved and verified")
    assert deactivation["is_active"] is False
    assert mgr.is_kill_switch_active() is False

    # Now publishing succeeds again
    res2 = publisher.publish_candidate(candidate_2.id, operator_id="admin_1")
    assert res2["status"] == "published"
