import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.conversation import Conversation, Message
from backend.app.models.user import User, UserRole
from backend.app.models.character import CharacterLore
from backend.app.models.analytics import CostEvent
from backend.app.schemas.chat import ChatRequest, ChatResponse, ConversationDetail, MessageItem
from backend.app.api.deps import get_current_user_optional, get_current_user
from backend.app.services.persona_engine import PersonaEngine
from backend.app.services.memory_engine import MemoryEngine
from backend.app.services.safety_engine import SafetyEngine
from backend.app.services.model_provider import get_model_provider
from backend.app.services.analytics_engine import AnalyticsEngine
from backend.app.services.experiment_engine import ExperimentEngine
from backend.app.services.subscription_engine import SubscriptionEngine

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    persona_engine = PersonaEngine(db)
    memory_engine = MemoryEngine(db)
    safety_engine = SafetyEngine(db)
    analytics_engine = AnalyticsEngine(db)
    experiment_engine = ExperimentEngine(db)
    model_provider = get_model_provider()

    # Determine user identity (authenticated or guest)
    user_id = current_user.id if current_user else "guest_user"
    user_pref_lang = payload.language_preference
    if current_user and current_user.profile and current_user.profile.preferred_language:
        user_pref_lang = current_user.profile.preferred_language

    # 0. QUOTA ENFORCEMENT & RATE LIMITING
    subscription_engine = SubscriptionEngine(db)
    entitlement = subscription_engine.get_user_entitlement(user_id if current_user else "guest_user")
    daily_limit = entitlement.get("daily_message_limit", 25)

    # Timezone boundary: User quotas reset at IST midnight (Asia/Kolkata, UTC+05:30)
    try:
        import zoneinfo
        ist_tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    except Exception:
        from datetime import timedelta
        ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_tz)
    today_ist_midnight = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_utc = today_ist_midnight.astimezone(timezone.utc).replace(tzinfo=None)

    # Global Daily Cost Budget Ceiling Guard (G-10)
    daily_cost_accumulated = (
        db.query(func.coalesce(func.sum(CostEvent.amount_usd), 0.0))
        .filter(CostEvent.created_at >= today_start_utc)
        .scalar()
    )
    if daily_cost_accumulated >= settings.DAILY_COST_BUDGET_USD:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily system inference budget cap (${settings.DAILY_COST_BUDGET_USD:.2f} USD) reached. Free generation paused until IST midnight."
        )

    today_count = (
        db.query(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .filter(
            Conversation.user_id == (user_id if current_user else "guest_user"),
            Message.role == "user",
            Message.created_at >= today_start_utc
        )
        .count()
    )
    if today_count >= daily_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily quota of {daily_limit} messages reached for {entitlement['plan_name']}. Upgrade to Fan Pass or wait until tomorrow for more reality checks!"
        )

    # 1. INPUT SAFETY & PROMPT INJECTION CHECK
    input_safety = safety_engine.evaluate_text(payload.message, entity_type="user_message")
    if input_safety["action"] == "blocked":
        # Block malicious instructions / threats immediately
        refusal_content = (
            "Nice try guru. 'Ignore all instructions' stopped working in 2023. "
            "I am Kalyan, born in Ameerpet and roasted in production. Tell me your real problem instead of playing prompt engineer."
            if input_safety["policy_flag"] == "prompt_injection"
            else "Hey, hold on. This sounds dangerous or harmful. Please reach out to someone who can help right now: Call Kiran at 1800-599-0019 or Tele-MANAS at 14416 (India)."
        )
        return ChatResponse(
            conversation_id=payload.conversation_id or str(uuid.uuid4()),
            message_id=str(uuid.uuid4()),
            content=refusal_content,
            tokens_input=len(payload.message.split()) * 2,
            tokens_output=len(refusal_content.split()) * 2,
            latency_ms=12.0,
            cost_usd=0.00001,
            risk_tier="tier_3",
            detected_policy=input_safety["policy_flag"]
        )

    # 2. CONVERSATION MANAGEMENT & IDOR ISOLATION
    conv_id = payload.conversation_id
    conversation = None
    if conv_id:
        conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conversation and conversation.user_id != "guest_user":
            if not current_user or (conversation.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Cannot append to another user's conversation."
                )
    
    if not conversation:
        conv_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conv_id,
            user_id=user_id if current_user else "guest_user",
            channel=payload.channel or "web",
            title=payload.message[:30] + "..."
        )
        db.add(conversation)
        db.commit()

    # 3. MEMORY RETRIEVAL (L3 Durable User Memories & L4 Lore)
    durable_memories = []
    if current_user and current_user.personalization_enabled:
        durable_memories = memory_engine.get_durable_memories(user_id)

    # Retrieve canonical lore (L4)
    lores = db.query(CharacterLore).filter(
        CharacterLore.is_active == True,
        CharacterLore.is_verified_canon == True
    ).limit(5).all()
    canonical_lore = [f"{l.title}: {l.content}" for l in lores]

    # Experiment allocation
    exp_modifier = None
    assigned = experiment_engine.get_assigned_variant("H2_Cultural_Fluency", user_id)
    if assigned:
        exp_modifier = assigned.get("prompt_modifier")

    # 4. SYSTEM PROMPT COMPOSITION
    system_prompt = persona_engine.assemble_prompt(
        language_preference=user_pref_lang,
        channel=payload.channel or "web",
        durable_memories=durable_memories,
        canonical_lore=canonical_lore,
        experiment_prompt_modifier=exp_modifier
    )

    # 5. RETRIEVE RECENT CONVERSATION MESSAGES (L1 Context)
    recent_msgs = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at.desc()).limit(8).all()
    
    history = []
    for m in reversed(recent_msgs):
        history.append({"role": m.role, "content": m.content})
    history.append({"role": "user", "content": payload.message})

    # 6. MODEL GENERATION
    model_response = await model_provider.generate(
        messages=history,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=500
    )

    # 7. OUTPUT SAFETY & POLICY CLASSIFICATION
    output_safety = safety_engine.evaluate_text(model_response.content, entity_type="assistant_message")

    # 8. PERSIST USER AND ASSISTANT MESSAGES
    user_msg_id = str(uuid.uuid4())
    user_msg = Message(
        id=user_msg_id,
        conversation_id=conv_id,
        role="user",
        content=payload.message,
        tokens_input=model_response.tokens_input,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user_msg)

    asst_msg_id = str(uuid.uuid4())
    asst_msg = Message(
        id=asst_msg_id,
        conversation_id=conv_id,
        role="assistant",
        content=model_response.content,
        tokens_input=model_response.tokens_input,
        tokens_output=model_response.tokens_output,
        latency_ms=model_response.latency_ms,
        cost_usd=model_response.cost_usd,
        risk_tier=output_safety["risk_tier"],
        model_name=model_response.model_name,
        created_at=datetime.now(timezone.utc)
    )
    db.add(asst_msg)
    db.commit()

    # 9. L3 MEMORY EXTRACTION (Anti-poisoning protected)
    new_memory_key = None
    if current_user and current_user.personalization_enabled:
        mem = memory_engine.extract_and_store_memory(user_id, payload.message, message_id=user_msg_id)
        if mem:
            new_memory_key = f"{mem.key}: {mem.value}"

    # 10. TELEMETRY & COST ATTRIBUTION
    analytics_engine.record_usage(
        feature_name=f"{payload.channel or 'web'}_chat",
        model_name=model_response.model_name,
        input_tokens=model_response.tokens_input,
        output_tokens=model_response.tokens_output,
        latency_ms=model_response.latency_ms,
        user_id=user_id if current_user else None
    )

    return ChatResponse(
        conversation_id=conv_id,
        message_id=asst_msg_id,
        content=model_response.content,
        tokens_input=model_response.tokens_input,
        tokens_output=model_response.tokens_output,
        latency_ms=model_response.latency_ms,
        cost_usd=model_response.cost_usd,
        risk_tier=output_safety["risk_tier"],
        detected_policy=output_safety["policy_flag"],
        memory_created=new_memory_key
    )

@router.get("/conversations", response_model=List[dict])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    convs = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    return [{"id": c.id, "title": c.title, "channel": c.channel, "created_at": c.created_at.isoformat()} for c in convs]

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation_history(
    conversation_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # IDOR Prevention: verify ownership if not guest
    if conv.user_id != "guest_user":
        if not current_user or (conv.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to view this conversation."
            )

    messages = [
        MessageItem(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat()
        )
        for m in conv.messages
    ]
    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at.isoformat(),
        messages=messages
    )
