import hmac
import hashlib
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.subscription import PaymentTransaction
from backend.app.api.deps import get_current_user
from backend.app.services.subscription_engine import SubscriptionEngine, TIER_PLANS

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

class CheckoutPayload(BaseModel):
    plan_tier: str

@router.get("/plans")
def get_plans():
    return [
        {
            "tier_key": k,
            "name": v["name"],
            "price_inr": v["price_inr"],
            "daily_limit": v["daily_message_limit"],
            "has_priority_memory": v["has_priority_memory"],
            "has_voice": v["has_voice"]
        }
        for k, v in TIER_PLANS.items()
    ]

@router.get("/my-entitlement")
def get_my_entitlement(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = SubscriptionEngine(db)
    return engine.get_user_entitlement(current_user.id)

@router.post("/checkout")
def checkout(
    payload: CheckoutPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = SubscriptionEngine(db)
    try:
        result = engine.process_checkout(current_user.id, payload.plan_tier)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    body_bytes = await request.body()
    
    # 1. HMAC signature verification
    if not x_razorpay_signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
        
    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body_bytes,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_signature, x_razorpay_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON payload")
        
    engine = SubscriptionEngine(db)
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    payment_id = payment_entity.get("id") or payload.get("payment_id")
    user_id = payment_entity.get("notes", {}).get("user_id") or payload.get("user_id")
    plan_tier = payment_entity.get("notes", {}).get("plan_tier") or payload.get("plan_tier", "fan_pass_149")
    
    if not payment_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing payment_id or user_id in webhook payload")
        
    # 2. Idempotency check: prevent replay double-crediting
    existing_txn = db.query(PaymentTransaction).filter(PaymentTransaction.payment_reference == payment_id).first()
    if existing_txn:
        return {"status": "ok", "message": "Transaction already processed (idempotent replay skipped)", "payment_id": payment_id}
        
    # Process new subscription
    res = engine.process_checkout(user_id, plan_tier)
    txn = db.query(PaymentTransaction).filter(PaymentTransaction.payment_reference == res["payment_reference"]).first()
    if txn:
        txn.payment_reference = payment_id
        db.commit()
        
    return {"status": "ok", "message": "Payment verified and subscription activated", "payment_id": payment_id}
