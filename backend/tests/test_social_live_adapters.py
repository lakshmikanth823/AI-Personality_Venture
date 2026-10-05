import pytest
from unittest.mock import patch, MagicMock
from backend.app.core.config import settings
from backend.app.services.social_gateway import (
    XAdapter,
    InstagramAdapter,
    YouTubeAdapter,
    WhatsAppAdapter
)

def test_x_adapter_staged_and_live():
    adapter = XAdapter()
    
    # 1. Staged mode (default without live broadcast flag)
    res_staged = adapter.publish("Kalyan says: Ship code instead of attending 3-hour meetings.")
    assert res_staged["platform"] == "x"
    assert res_staged["status"] == "published"
    assert res_staged["mode"] == "staged_simulated"
    assert "kalyan_unfiltered" in res_staged["url"]

    # 2. Live mode with mocked httpx response
    with patch.object(settings, "ENABLE_LIVE_SOCIAL_BROADCAST", True), \
         patch.object(settings, "X_ACCESS_TOKEN", "mock_live_x_token_123"):
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"data": {"id": "1899999999999999999", "text": "Test tweet"}}

        with patch("httpx.post", return_value=mock_response):
            res_live = adapter.publish("Live test tweet")
            assert res_live["status"] == "published"
            assert res_live["mode"] == "live_broadcast"
            assert res_live["external_id"] == "1899999999999999999"

def test_instagram_adapter_staged_and_live():
    adapter = InstagramAdapter()
    
    # Staged mode
    res_staged = adapter.publish("Irani chai > Matcha latte. Change my mind.")
    assert res_staged["platform"] == "instagram"
    assert res_staged["status"] == "published"
    assert res_staged["mode"] == "staged_simulated"

    # Live mode with mock
    with patch.object(settings, "ENABLE_LIVE_SOCIAL_BROADCAST", True), \
         patch.object(settings, "INSTAGRAM_ACCESS_TOKEN", "mock_ig_token"), \
         patch.object(settings, "INSTAGRAM_PAGE_ID", "123456789"):
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "ig_live_post_77777"}

        with patch("httpx.post", return_value=mock_resp):
            res_live = adapter.publish("Live IG caption")
            assert res_live["mode"] == "live_broadcast"
            assert res_live["external_id"] == "ig_live_post_77777"

def test_youtube_adapter_staged_and_live():
    adapter = YouTubeAdapter()
    
    # Staged mode
    res_staged = adapter.publish("Why your resume gets rejected in 6 seconds.")
    assert res_staged["platform"] == "youtube"
    assert res_staged["status"] == "published"

    # Live mode with mock
    with patch.object(settings, "ENABLE_LIVE_SOCIAL_BROADCAST", True), \
         patch.object(settings, "YOUTUBE_API_KEY", "mock_yt_key"):
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "yt_video_99999"}

        with patch("httpx.post", return_value=mock_resp):
            res_live = adapter.publish("Live YT Short title")
            assert res_live["mode"] == "live_broadcast"
            assert res_live["external_id"] == "yt_video_99999"

def test_whatsapp_adapter_staged_and_live():
    adapter = WhatsAppAdapter()
    
    # Staged mode
    res_staged = adapter.publish("Dost, did you apply for that job today or are you still overthinking?")
    assert res_staged["platform"] == "whatsapp"
    assert res_staged["status"] == "sent"

    # Live mode with mock
    with patch.object(settings, "ENABLE_LIVE_SOCIAL_BROADCAST", True), \
         patch.object(settings, "WHATSAPP_TOKEN", "mock_wa_token"), \
         patch.object(settings, "WHATSAPP_PHONE_NUMBER_ID", "987654321"):
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"messages": [{"id": "wamid.HBgL..."}]}

        with patch("httpx.post", return_value=mock_resp):
            res_live = adapter.publish("Live WhatsApp check-in")
            assert res_live["mode"] == "live_broadcast"
            assert res_live["external_id"] == "wamid.HBgL..."

def test_meta_webhook_verification_and_event_ingestion(client):
    # 1. Meta Webhook challenge verification (GET handshake)
    challenge_res = client.get(
        "/api/v1/publisher/webhook/meta?hub_mode=subscribe&hub_verify_token=kalyan_wa_verify_2026&hub_challenge=1158201444"
    )
    assert challenge_res.status_code == 200
    assert challenge_res.text == "1158201444"

    # Bad verify token -> 403
    bad_res = client.get("/api/v1/publisher/webhook/meta?hub_mode=subscribe&hub_verify_token=wrong_token")
    assert bad_res.status_code == 403

    # 2. Inbound WhatsApp message event (POST event)
    event_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "wa_acc_1",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "+919876543210",
                        "id": "wamid.ABGG...",
                        "timestamp": "1728100000",
                        "text": {"body": "Kalyan bro, should I quit TCS and join an early stage startup?"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    ingest_res = client.post("/api/v1/publisher/webhook/meta", json=event_payload)
    assert ingest_res.status_code == 200
    data = ingest_res.json()
    assert data["status"] == "processed"
    assert data["ingested_count"] == 1
    assert data["items"][0]["status"] == "queued"
    assert "candidate_id" in data["items"][0]
