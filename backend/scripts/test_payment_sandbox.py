"""
backend/scripts/test_payment_sandbox.py
Verifies end-to-end sandbox payment flows, HMAC signature verification,
idempotency replay defense, and user entitlement upgrades.
"""

import sys
import os
import time
import json
import uuid
import hmac
import hashlib
import random
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import httpx
from backend.app.core.config import settings

BASE_URL = "http://127.0.0.1:8000"

def run_payment_sandbox_suite():
    print("=" * 70)
    print("  PHASE 6.3: PAYMENT SANDBOX & WEBHOOK INTEGRATION SUITE")
    print("=" * 70)
    
    sim_ip = f"10.150.{random.randint(1, 250)}.{random.randint(1, 250)}"
    with httpx.Client(base_url=BASE_URL, timeout=15.0, headers={"X-Forwarded-For": sim_ip}) as client:
        # 1. Fetch Subscription Plans
        r_plans = client.get("/api/v1/subscriptions/plans")
        assert r_plans.status_code == 200
        plans = r_plans.json()
        print(f"[1] Plans Fetched: {len(plans)} active tiers found.")
        for p in plans:
            print(f"    - {p['name']} ({p['tier_key']}): Rs. {p['price_inr']} | {p['daily_limit']} msgs/day")
            
        # 2. Register Staging Subscriber User
        uname = f"payer_{uuid.uuid4().hex[:6]}"
        r_signup = client.post("/api/v1/auth/signup", json={
            "email": f"{uname}@kalyan-ai.staging",
            "username": uname,
            "password": "PaymentTest2026!",
            "display_name": "Rajesh Payer",
            "preferred_language": "hinglish"
        })
        assert r_signup.status_code == 200
        user_data = r_signup.json()
        user_id = user_data["user_id"]
        auth_headers = {"Authorization": f"Bearer {user_data['access_token']}"}
        print(f"\n[2] User Registered: {uname} (ID: {user_id})")
        
        # 3. Check Initial Entitlement (Free Tier)
        r_ent_init = client.get("/api/v1/subscriptions/my-entitlement", headers=auth_headers)
        assert r_ent_init.status_code == 200
        ent_init = r_ent_init.json()
        print(f"[3] Initial Entitlement: Tier='{ent_init['plan_name']}' ({ent_init['tier']}), Daily Limit={ent_init['daily_message_limit']}")
        assert ent_init["tier"] == "free"
        assert ent_init["daily_message_limit"] == 25
        
        # 4. Initiate Sandbox Checkout
        r_checkout = client.post("/api/v1/subscriptions/checkout", json={"plan_tier": "fan_pass_149"}, headers=auth_headers)
        assert r_checkout.status_code == 200
        checkout_data = r_checkout.json()
        print(f"[4] Checkout Initiated: Plan='{checkout_data['plan_tier']}', Price=Rs.{checkout_data['amount_inr']}, Ref={checkout_data['payment_reference']}")
        
        # 5. Simulate Razorpay Webhook Event with HMAC Signature
        payment_id = f"pay_sandbox_{uuid.uuid4().hex[:12]}"
        webhook_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": payment_id,
                        "amount": 14900,
                        "currency": "INR",
                        "status": "captured",
                        "notes": {
                            "user_id": user_id,
                            "plan_tier": "fan_pass_149"
                        }
                    }
                }
            }
        }
        payload_bytes = json.dumps(webhook_payload).encode("utf-8")
        valid_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        r_webhook = client.post(
            "/api/v1/subscriptions/webhook",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": valid_signature
            }
        )
        assert r_webhook.status_code == 200
        print(f"\n[5] Webhook Verified & Processed: HTTP {r_webhook.status_code}")
        print(f"    Response: {r_webhook.json()}")
        
        # 6. Verify Entitlement Upgrade
        r_ent_upgraded = client.get("/api/v1/subscriptions/my-entitlement", headers=auth_headers)
        assert r_ent_upgraded.status_code == 200
        ent_upgraded = r_ent_upgraded.json()
        print(f"\n[6] Upgraded Entitlement: Tier='{ent_upgraded['plan_name']}' ({ent_upgraded['tier']}), Daily Limit={ent_upgraded['daily_message_limit']}")
        assert ent_upgraded["tier"] == "fan_pass_149"
        assert ent_upgraded["daily_message_limit"] == 500
        assert ent_upgraded["has_voice"] is True
        assert ent_upgraded["has_priority_memory"] is True
        
        # 7. Test Idempotency Replay Defense
        r_replay = client.post(
            "/api/v1/subscriptions/webhook",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": valid_signature
            }
        )
        assert r_replay.status_code == 200
        replay_resp = r_replay.json()
        print(f"\n[7] Replay Defense Test: HTTP {r_replay.status_code}")
        print(f"    Message: {replay_resp['message']} (Idempotent: { 'idempotent' in replay_resp['message'].lower() })")
        assert "idempotent" in replay_resp["message"].lower()
        
        # 8. Test Invalid Signature Rejection (Tampered Webhook)
        invalid_sig = "bad_tampered_signature_999"
        r_tampered = client.post(
            "/api/v1/subscriptions/webhook",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": invalid_sig
            }
        )
        assert r_tampered.status_code == 401
        print(f"\n[8] Tampered Signature Rejection: HTTP {r_tampered.status_code} (Unauthorized - Correctly Blocked)")
        
    print("\n" + "=" * 70)
    print("  ALL PAYMENT SANDBOX TESTS PASSED (100% REAL-PASS)")
    print("=" * 70)
    return True

if __name__ == "__main__":
    run_payment_sandbox_suite()
