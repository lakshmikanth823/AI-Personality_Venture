import pytest
import uuid
from datetime import datetime, timezone
from backend.app.services.analytics_engine import AnalyticsEngine
from backend.app.models.conversation import Conversation, Message
from backend.app.models.user import User, UserRole
from backend.app.core.security import get_password_hash

def test_usage_and_cost_recording(db_session):
    engine = AnalyticsEngine(db_session)
    event = engine.record_usage(
        feature_name="web_chat",
        model_name="kalyan-orchestrator-v1",
        input_tokens=500,
        output_tokens=150,
        latency_ms=120.5
    )
    assert event.input_tokens == 500
    assert event.output_tokens == 150
    assert event.cost_usd > 0.0

def test_wmcr_calculation(db_session):
    engine = AnalyticsEngine(db_session)

    # Create user with 3 distinct interactions within 7 days
    u = User(
        id=str(uuid.uuid4()),
        email="wmcr_user@test.com",
        username="wmcr_user",
        hashed_password=get_password_hash("pass123"),
        role=UserRole.USER
    )
    db_session.add(u)
    db_session.commit()

    conv = Conversation(
        id=str(uuid.uuid4()),
        user_id=u.id,
        channel="web",
        title="WMCR Test"
    )
    db_session.add(conv)
    db_session.commit()

    # Add 3 user messages
    for i in range(3):
        m = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="user",
            content=f"Message {i}",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(m)
    db_session.commit()

    wmcr = engine.calculate_wmcr()
    assert wmcr == 1

def test_dashboard_metrics(db_session):
    engine = AnalyticsEngine(db_session)
    metrics = engine.get_dashboard_metrics()
    assert "north_star_wmcr" in metrics
    assert "total_tokens_processed" in metrics
    assert "total_cost_usd" in metrics
    assert "contribution_margin_inr" in metrics
    assert len(metrics["strategic_insights"]) > 0
