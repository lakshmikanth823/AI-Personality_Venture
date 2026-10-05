import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.subscription import Subscription, PaymentTransaction
from backend.app.models.user import User

TIER_PLANS = {
    "free": {
        "name": "Free Dost",
        "price_inr": 0,
        "daily_message_limit": 25,
        "has_priority_memory": False,
        "has_voice": False
    },
    "single_roast_49": {
        "name": "Filterless Reality Check (Single Pass)",
        "price_inr": 49,
        "daily_message_limit": 100,
        "has_priority_memory": True,
        "has_voice": False
    },
    "fan_pass_149": {
        "name": "Kalyan Fan Pass (Monthly)",
        "price_inr": 149,
        "daily_message_limit": 500,
        "has_priority_memory": True,
        "has_voice": True,
        "duration_days": 30
    },
    "vip_insider_299": {
        "name": "VIP Inner Circle (Monthly)",
        "price_inr": 299,
        "daily_message_limit": 2000,
        "has_priority_memory": True,
        "has_voice": True,
        "duration_days": 30
    },
    "custom_lore_999": {
        "name": "Canonical Lore Feature",
        "price_inr": 999,
        "daily_message_limit": 5000,
        "has_priority_memory": True,
        "has_voice": True,
        "duration_days": 90
    }
}

class SubscriptionEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_user_entitlement(self, user_id: str) -> Dict[str, Any]:
        sub = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active"
        ).order_by(Subscription.started_at.desc()).first()

        tier_key = sub.plan_tier if sub else "free"
        plan = TIER_PLANS.get(tier_key, TIER_PLANS["free"])

        return {
            "tier": tier_key,
            "plan_name": plan["name"],
            "price_inr": plan["price_inr"],
            "daily_message_limit": plan["daily_message_limit"],
            "has_priority_memory": plan["has_priority_memory"],
            "has_voice": plan["has_voice"],
            "expires_at": sub.expires_at.isoformat() if (sub and sub.expires_at) else None
        }

    def process_checkout(self, user_id: str, plan_tier: str) -> Dict[str, Any]:
        if plan_tier not in TIER_PLANS:
            raise ValueError(f"Invalid plan tier: {plan_tier}")

        plan = TIER_PLANS[plan_tier]
        amount = plan["price_inr"]
        ref_id = f"pay_{uuid.uuid4().hex[:12]}"

        duration_days = plan.get("duration_days", 30)
        expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)

        # Create or update subscription
        existing_sub = self.db.query(Subscription).filter(Subscription.user_id == user_id).first()
        if existing_sub:
            existing_sub.plan_tier = plan_tier
            existing_sub.status = "active"
            existing_sub.started_at = datetime.now(timezone.utc)
            existing_sub.expires_at = expires_at
            existing_sub.total_paid_inr += amount
            sub_id = existing_sub.id
        else:
            new_sub = Subscription(
                id=str(uuid.uuid4()),
                user_id=user_id,
                plan_tier=plan_tier,
                status="active",
                started_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                total_paid_inr=amount
            )
            self.db.add(new_sub)
            self.db.flush()
            sub_id = new_sub.id

        # Record payment transaction
        txn = PaymentTransaction(
            id=str(uuid.uuid4()),
            subscription_id=sub_id,
            user_id=user_id,
            plan_tier=plan_tier,
            amount_inr=amount,
            currency="INR",
            status="completed",
            payment_reference=ref_id,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(txn)
        self.db.commit()

        return {
            "success": True,
            "payment_reference": ref_id,
            "plan_tier": plan_tier,
            "amount_inr": amount,
            "status": "completed",
            "message": f"Successfully subscribed to {plan['name']}!"
        }
