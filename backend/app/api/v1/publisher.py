from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.content import PublishedAction
from backend.app.api.deps import require_role
from backend.app.services.social_gateway import SocialPublisherService, SocialPublishError

router = APIRouter(prefix="/publisher", tags=["publisher"])

class IngestMentionRequest(BaseModel):
    channel: str = "x" # x, instagram, whatsapp, youtube
    author: str
    content: str
    external_id: Optional[str] = None

@router.post("/publish/{candidate_id}")
def publish_candidate(
    candidate_id: str,
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    publisher = SocialPublisherService(db)
    try:
        result = publisher.publish_candidate(candidate_id, operator_id=current_user.id)
        return result
    except SocialPublishError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/published-history")
def get_published_history(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    actions = db.query(PublishedAction).order_by(PublishedAction.published_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "candidate_id": a.candidate_id,
            "channel": a.channel,
            "external_post_id": a.external_post_id,
            "published_at": a.published_at.isoformat(),
            "status": a.status,
            "error_message": a.error_message
        }
        for a in actions
    ]

@router.post("/ingest-mention")
def ingest_social_mention(
    payload: IngestMentionRequest,
    db: Session = Depends(get_db)
):
    """
    Channel Gateway for incoming social mentions/interactions:
    Ingest -> Classify -> Generate draft candidate -> Route based on Risk Tier.
    """
    from backend.app.services.safety_engine import SafetyEngine
    from backend.app.models.content import ContentCandidate
    from backend.app.services.persona_engine import PersonaEngine
    import uuid
    from datetime import datetime, timezone

    safety_engine = SafetyEngine(db)
    safety_eval = safety_engine.evaluate_text(payload.content, entity_type="social_mention")

    # Draft candidate reply
    reply_text = f"@{payload.author} Let's be real: {payload.content.strip()[:60]}... Overthinking this won't fix it. Take action guru."
    cand_id = str(uuid.uuid4())

    candidate = ContentCandidate(
        id=cand_id,
        source_channel=payload.channel,
        pillar="user_situations",
        format="reply",
        raw_prompt=f"Reply to {payload.author}: '{payload.content}'",
        candidate_text=reply_text,
        risk_tier=safety_eval["risk_tier"],
        safety_evaluation_json=str(safety_eval),
        status="pending_approval" if safety_eval["risk_tier"] != "tier_0" else "approved",
        created_at=datetime.now(timezone.utc)
    )
    db.add(candidate)
    db.commit()

    return {
        "status": "queued",
        "candidate_id": cand_id,
        "risk_tier": safety_eval["risk_tier"],
        "assigned_route": "auto_approved" if safety_eval["risk_tier"] == "tier_0" else "human_approval_required",
        "draft_reply": reply_text
    }

@router.get("/webhook/meta")
def meta_webhook_verification(
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Standard Meta Graph API Webhook Challenge Verification for Instagram & WhatsApp.
    """
    from backend.app.core.config import settings
    from fastapi.responses import PlainTextResponse
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge or "")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("/webhook/meta")
def meta_webhook_event(
    event_payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Ingests live incoming WhatsApp messages or Instagram comments/mentions.
    """
    # Extract entry items
    entries = event_payload.get("entry", [])
    ingested = []
    for entry in entries:
        changes = entry.get("changes", [])
        for ch in changes:
            val = ch.get("value", {})
            messages = val.get("messages", [])
            for msg in messages:
                sender = msg.get("from", "unknown_user")
                body = msg.get("text", {}).get("body", "")
                if body:
                    req = IngestMentionRequest(channel="whatsapp", author=sender, content=body)
                    res = ingest_social_mention(req, db)
                    ingested.append(res)
    return {"status": "processed", "ingested_count": len(ingested), "items": ingested}
