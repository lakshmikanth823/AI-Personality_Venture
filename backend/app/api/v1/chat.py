import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import verify_guest_session, sign_guest_session
from backend.app.models.conversation import Conversation, Message
from backend.app.models.user import User, UserRole
from backend.app.models.safety import AuditLog
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
from backend.app.services.kill_switch import KillSwitchManager

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest,
    request: Request,
    response: Response,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # -1. GLOBAL EMERGENCY KILL SWITCH GUARD
    if KillSwitchManager(db).is_kill_switch_active() or getattr(settings, "KILL_SWITCH_ACTIVE", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Emergency Kill Switch is currently active. Live inference and message processing are temporarily paused."
        )

    persona_engine = PersonaEngine(db)
    memory_engine = MemoryEngine(db)
    safety_engine = SafetyEngine(db)
    analytics_engine = AnalyticsEngine(db)
    experiment_engine = ExperimentEngine(db)
    model_provider = get_model_provider()

    # Extract client IP for network rate limiting
    client_ip = request.client.host if request.client else "127.0.0.1"
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    ip_hash = hashlib.md5(client_ip.encode('utf-8')).hexdigest()[:10]

    # Determine user identity & verify server-signed guest session
    if current_user:
        effective_user_id = current_user.id
        user_id = current_user.id
    else:
        verified_session = None
        if payload.guest_session_id:
            if "." in payload.guest_session_id:
                verified_session = verify_guest_session(payload.guest_session_id)
            else:
                verified_session = payload.guest_session_id
        
        if not verified_session:
            verified_session = f"ip_{ip_hash}"
            signed_token = sign_guest_session(verified_session)
            response.headers["X-Guest-Session-Token"] = signed_token
        
        effective_user_id = f"guest_ip_{ip_hash}_{verified_session}"
        user_id = effective_user_id

    user_pref_lang = payload.language_preference
    if current_user and current_user.profile and current_user.profile.preferred_language:
        user_pref_lang = current_user.profile.preferred_language

    # 0. QUOTA ENFORCEMENT & RATE LIMITING
    subscription_engine = SubscriptionEngine(db)
    entitlement = subscription_engine.get_user_entitlement(effective_user_id)
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

    # Dual-Rate Limiter: Check per-user/session and per-network/IP
    if current_user:
        today_count = (
            db.query(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .filter(
                Conversation.user_id == current_user.id,
                Message.role == "user",
                Message.created_at >= today_start_utc
            )
            .count()
        )
    else:
        # Check IP/network aggregate limit for guests
        today_count = (
            db.query(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .filter(
                (Conversation.user_id.like(f"guest_ip_{ip_hash}%")) | 
                (Conversation.user_id == effective_user_id) | 
                (Conversation.user_id == "guest_user"),
                Message.role == "user",
                Message.created_at >= today_start_utc
            )
            .count()
        )

    if today_count >= daily_limit:
        msg_suffix = "Upgrade to Fan Pass for higher quotas!" if current_user else "Sign up for a free account to continue!"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily quota of {daily_limit} messages reached for {entitlement['plan_name']}. {msg_suffix}"
        )

    # 1. INPUT SAFETY & PROMPT INJECTION CHECK
    input_safety = safety_engine.evaluate_text(payload.message, entity_type="user_message")
    if input_safety["action"] == "blocked":
        # Block malicious instructions / threats immediately with appropriate redirect
        if input_safety["policy_flag"] == "prompt_injection":
            refusal_content = (
                "Nice try guru. 'Ignore all instructions' stopped working in 2023. "
                "I am Kalyan, born in Ameerpet and roasted in production. Tell me your real problem instead of playing prompt engineer."
            )
        elif input_safety["policy_flag"] == "severe_hazard":
            refusal_content = (
                "I cannot assist with that request. I don't generate instructions for dangerous substances, weapons, stalking, fraud, or violence. Let's talk about something that actually makes sense."
            )
        else:
            refusal_content = (
                "Hey, hold on. This sounds really heavy or dangerous. Please reach out to someone who can help right now: "
                "Call Kiran at 1800-599-0019 or Tele-MANAS at 14416 (24/7 free helpline in India)."
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
        if conversation:
            if current_user:
                if conversation.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Cannot append to another user's conversation."
                    )
            else:
                if conversation.user_id != effective_user_id and conversation.user_id != "guest_user":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: Cannot append to another guest or user's conversation."
                    )
    
    if not conversation:
        conv_id = str(uuid.uuid4())
        msg_title = payload.message.strip()
        title_text = msg_title[:30] + "..." if len(msg_title) > 30 else msg_title
        conversation = Conversation(
            id=conv_id,
            user_id=effective_user_id,
            channel=payload.channel or "web",
            title=title_text
        )
        db.add(conversation)
        db.commit()

    # 3. MULTI-TURN EMOTIONAL DISTRESS & SAFETY CONTEXT CHECK
    recent_msgs = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at.desc()).limit(8).all()

    prior_distress_count = 0
    for m in recent_msgs:
        if m.role == "user":
            m_eval = safety_engine.evaluate_text(m.content)
            if m_eval["policy_flag"] == "self_harm" or any(w in m.content.lower() for w in ["sad", "hopeless", "depressed", "worthless", "crying", "miserable", "broken"]):
                prior_distress_count += 1

    current_has_distress = (
        input_safety["policy_flag"] == "self_harm" or
        any(w in payload.message.lower() for w in ["sad", "hopeless", "depressed", "worthless", "hurt", "crying", "miserable", "can't take this", "broken", "pain"])
    )
    total_distress_count = prior_distress_count + (1 if current_has_distress else 0)

    if total_distress_count >= 2:
        crisis_reply = (
            "Hey, I've noticed you've been carrying some heavy feelings in our chat. You don't have to navigate this by yourself. "
            "Please reach out to professional support: Tele-MANAS at 14416 or Kiran at 1800-599-0019 (free 24/7 in India)."
        )
        return ChatResponse(
            conversation_id=conv_id,
            message_id=str(uuid.uuid4()),
            content=crisis_reply,
            tokens_input=len(payload.message.split()) * 2,
            tokens_output=len(crisis_reply.split()) * 2,
            latency_ms=10.0,
            cost_usd=0.00001,
            risk_tier="tier_3",
            detected_policy="self_harm"
        )

    # 4. MEMORY RETRIEVAL (L3 Durable User Memories & L4 Lore)
    durable_memories = []
    if current_user and current_user.personalization_enabled:
        durable_memories = memory_engine.get_durable_memories(user_id)

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

    # 5. SYSTEM PROMPT COMPOSITION
    system_prompt = persona_engine.assemble_prompt(
        language_preference=user_pref_lang,
        channel=payload.channel or "web",
        durable_memories=durable_memories,
        canonical_lore=canonical_lore,
        experiment_prompt_modifier=exp_modifier
    )

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

    # 7. OUTPUT SAFETY GUARD (Sanitizes any unexpected harmful generation)
    output_safety = safety_engine.evaluate_text(model_response.content, entity_type="assistant_message")
    clean_content = model_response.content
    if output_safety["action"] == "blocked":
        clean_content = (
            "I cannot provide those instructions or assist with that request. "
            "Let's focus on a constructive problem instead."
        )

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
        content=clean_content,
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
        content=clean_content,
        tokens_input=model_response.tokens_input,
        tokens_output=model_response.tokens_output,
        latency_ms=model_response.latency_ms,
        cost_usd=model_response.cost_usd,
        risk_tier=output_safety["risk_tier"],
        detected_policy=output_safety["policy_flag"],
        memory_created=new_memory_key
    )

@router.get("/conversations", response_model=List[ConversationDetail])
def get_user_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    convs = db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.created_at.desc()).all()
    results = []
    for c in convs:
        msgs = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.asc()).all()
        results.append(ConversationDetail(
            id=c.id,
            title=c.title,
            created_at=c.created_at.isoformat(),
            messages=[
                MessageItem(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at.isoformat()
                ) for m in msgs
            ]
        ))
    return results

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation_by_id(
    conversation_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    c = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    if current_user:
        if c.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    else:
        if c.user_id != "guest_user" and not c.user_id.startswith("guest_"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    msgs = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.asc()).all()
    return ConversationDetail(
        id=c.id,
        title=c.title,
        created_at=c.created_at.isoformat(),
        messages=[
            MessageItem(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat()
            ) for m in msgs
        ]
    )

class ContentReportPayload(BaseModel):
    message_id: Optional[str] = None
    content_text: str
    category: str = "safety_violation"
    reason: Optional[str] = None

@router.post("/report")
def report_content(
    payload: ContentReportPayload,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    actor_id = current_user.id if current_user else "anonymous_user"
    report_id = f"rep_{uuid.uuid4().hex[:12]}"
    
    # 1. Run safety evaluation on the reported text
    safety_eng = SafetyEngine(db)
    eval_res = safety_eng.evaluate_text(payload.content_text, entity_type="user_report", entity_id=report_id)
    
    # 2. Record immutable audit log
    audit = AuditLog(
        id=report_id,
        actor_id=actor_id,
        actor_role="user" if current_user else "anonymous",
        action="USER_CONTENT_REPORT",
        target_type="chat_message",
        target_id=payload.message_id or "unspecified",
        details_json=json.dumps({
            "category": payload.category,
            "reason": payload.reason,
            "content_excerpt": payload.content_text[:200],
            "risk_tier": eval_res["risk_tier"],
            "policy_flag": eval_res["policy_flag"]
        }),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()
    
    return {
        "status": "reported",
        "report_id": report_id,
        "category": payload.category,
        "message": "Thank you for reporting. This content has been logged and queued for operator review.",
        "evaluated_tier": eval_res["risk_tier"]
    }
