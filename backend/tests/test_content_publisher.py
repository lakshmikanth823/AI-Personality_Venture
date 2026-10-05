import pytest
from backend.app.services.content_engine import ContentEngine
from backend.app.services.social_gateway import SocialPublisherService

def test_generate_candidate_batch(db_session):
    engine = ContentEngine(db_session)
    batch = engine.generate_candidate_batch(count=3, channel="x")
    assert len(batch) == 3
    for c in batch:
        assert c["status"] == "pending_approval"
        assert c["risk_tier"] in ["tier_0", "tier_1", "tier_2"]
        assert len(c["text"]) > 10

def test_operator_approval_workflow(db_session):
    engine = ContentEngine(db_session)
    publisher = SocialPublisherService(db_session)

    batch = engine.generate_candidate_batch(count=1, channel="instagram")
    cand_id = batch[0]["id"]

    # Operator approves candidate with edit
    edited_text = "Edited by operator: Filter coffee is good, but Irani chai is legendary."
    approval_res = engine.approve_and_queue(cand_id, operator_id="op_1", final_text=edited_text)
    assert approval_res["status"] == "approved"
    assert approval_res["text"] == edited_text

    # Publish approved candidate
    pub_res = publisher.publish_candidate(cand_id, operator_id="op_1")
    assert pub_res["status"] == "published"
    assert pub_res["channel"] == "instagram"
    assert "instagram.com" in pub_res["url"]
