import hmac
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.subscription import Subscription, PaymentTransaction
from backend.app.services.subscription_engine import TIER_PLANS

class PaymentGatewayService:
    """
    Production-ready payment gateway scaffolding for Razorpay / Stripe webhooks.
    Includes HMAC-SHA256 signature verification, idempotency checking, and automatic entitlement activation.
    """
    def __init__(self, db: Session, webhook_secret: str = "rzp_webhook_secret_kalyan_2026"):
        self.db = db
        self.webhook_secret = webhook_secret

    def verify_webhook_signature(self, body_bytes: bytes, received_signature: str, secret: Optional[str] = None) -> bool:
        sec = secret or self.webhook_secret
        expected_signature = hmac.new(
            sec.encode('utf-8'),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, received_signature)

    def verify_razorpay_signature(self, body_bytes: bytes, received_signature: str) -> bool:
        return self.verify_webhook_signature(body_bytes, received_signature)

    def process_verified_payment(self, event_payload: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        payment_id = event_payload.get("payment_id", str(uuid.uuid4()))
        plan_tier = event_payload.get("plan_tier", "fan_pass_149")
        if plan_tier == "fan_pass":
            plan_tier = "fan_pass_149"
        
        existing_txn = self.db.query(PaymentTransaction).filter(
            PaymentTransaction.payment_reference == payment_id
        ).first()
        if existing_txn:
            return {"status": "already_processed", "duplicate": True, "payment_reference": payment_id}

        event_data = {
            "payload": {
                "payment": {
                    "entity": {
                        "id": payment_id,
                        "amount": 14900,
                        "notes": {"user_id": user_id, "plan_tier": plan_tier}
                    }
                }
            }
        }
        return self.process_webhook_event(event_data)

    def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Idempotent payment webhook event handler.
        Example event: {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_xyz123",
                        "amount": 14900, # paise (₹149)
                        "notes": {"user_id": "u1", "plan_tier": "fan_pass_149"}
                    }
                }
            }
        }
        """
        payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
        payment_id = payment_entity.get("id", str(uuid.uuid4()))
        notes = payment_entity.get("notes", {})
        user_id = notes.get("user_id")
        plan_tier = notes.get("plan_tier", "fan_pass_149")
        amount_inr = payment_entity.get("amount", 14900) / 100.0

        if not user_id:
            return {"status": "ignored", "reason": "No user_id in payment notes"}

        # Idempotency check: if transaction already processed, do not double-credit
        existing_txn = self.db.query(PaymentTransaction).filter(
            PaymentTransaction.payment_reference == payment_id
        ).first()
        if existing_txn:
            return {"status": "duplicate_ignored", "payment_reference": payment_id}

        # Activate or upgrade subscription
        plan = TIER_PLANS.get(plan_tier, TIER_PLANS["fan_pass_149"])
        duration_days = plan.get("duration_days", 30)
        expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)

        sub = self.db.query(Subscription).filter(Subscription.user_id == user_id).first()
        if sub:
            sub.plan_tier = plan_tier
            sub.status = "active"
            sub.started_at = datetime.now(timezone.utc)
            sub.expires_at = expires_at
            sub.total_paid_inr += amount_inr
            sub_id = sub.id
        else:
            new_sub = Subscription(
                id=str(uuid.uuid4()),
                user_id=user_id,
                plan_tier=plan_tier,
                status="active",
                started_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                total_paid_inr=amount_inr
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
            amount_inr=amount_inr,
            currency="INR",
            status="completed",
            payment_reference=payment_id,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(txn)
        self.db.commit()

        return {
            "status": "activated",
            "user_id": user_id,
            "plan_tier": plan_tier,
            "payment_reference": payment_id,
            "expires_at": expires_at.isoformat()
        }
