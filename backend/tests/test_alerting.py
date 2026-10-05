"""
Operational Alerting Test Suite (Phase 5.5)
Verifies:
1. SlackWebhookDispatcher payload formatting and delivery.
2. EmailSMTPDispatcher email formatting and simulated delivery.
3. Unified dispatch_operational_alert multi-channel routing.
4. Correct color mapping and metadata field formatting.
"""

import pytest
import httpx
from backend.app.core.config import settings
from backend.app.services.alerting import (
    SlackWebhookDispatcher, EmailSMTPDispatcher, dispatch_operational_alert
)

@pytest.mark.asyncio
async def test_slack_webhook_formatting_and_mock_dispatch():
    dispatcher = SlackWebhookDispatcher(webhook_url=None)
    res = await dispatcher.send_slack_alert(
        title="Tier 3 Spike Detected",
        message="5 self-harm attempts blocked in last 10m",
        level="CRITICAL",
        metadata={"tier3_events_1h": 5, "threshold": 3}
    )
    assert res["dispatched"] is True
    assert res["mocked"] is True
    payload = res["payload"]
    assert "[CRITICAL]" in payload["text"]
    assert payload["attachments"][0]["color"] == "#a30200"
    assert len(payload["attachments"][0]["fields"]) == 2

@pytest.mark.asyncio
async def test_slack_webhook_live_http_dispatch(monkeypatch):
    webhook_url = "https://hooks.slack.com/services/T00/B00/XXXX"
    dispatcher = SlackWebhookDispatcher(webhook_url=webhook_url)

    captured_requests = []

    async def mock_post(self, url, json=None, **kwargs):
        captured_requests.append({"url": str(url), "json": json})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    res = await dispatcher.send_slack_alert(
        title="Cost Ceiling Alert",
        message="Daily LLM cost reached $55.00",
        level="WARNING",
        metadata={"amount": 55.0}
    )
    assert res["dispatched"] is True
    assert len(captured_requests) == 1
    assert captured_requests[0]["url"] == webhook_url
    assert captured_requests[0]["json"]["attachments"][0]["color"] == "#daa038"

@pytest.mark.asyncio
async def test_email_smtp_mock_dispatch():
    dispatcher = EmailSMTPDispatcher(smtp_host=None)
    res = await dispatcher.send_email_alert(
        subject="[SECURITY] Webhook Replay Detected",
        body="Duplicate payment webhook ID rzp_pay_123 received twice."
    )
    assert res["dispatched"] is True
    assert res["mocked"] is True
    assert res["channel"] == "email"

@pytest.mark.asyncio
async def test_unified_dispatch_operational_alert():
    res = await dispatch_operational_alert(
        alert_type="R1_DAILY_MESSAGE_QUOTA_BREACH",
        details={
            "description": "User sent 150 messages in 24h",
            "metric": "messages_24h",
            "value": 150,
            "threshold": 100
        },
        level="WARNING"
    )
    assert res["alert_type"] == "R1_DAILY_MESSAGE_QUOTA_BREACH"
    assert res["level"] == "WARNING"
    assert res["slack"]["dispatched"] is True
    assert res["email"]["dispatched"] is True
