from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
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
