# E-31: Payment Gateway Sandbox & HMAC Verification

**Date:** 2026-10-05  
**Phase:** 6 — Controlled Production Activation  
**Gate:** Payment Sandbox / HMAC Webhooks  
**Status:** **PASS** (Cryptographic webhook signature & entitlement logic) / **EXTERNAL-BLOCKED** (Live Razorpay API sandbox credentials)

---

## 1. Webhook Signature & Security Hardening

In [`backend/app/api/v1/subscriptions.py`](file:///E:/per_char/backend/app/api/v1/subscriptions.py):
- **HMAC-SHA256 Verification**: Every incoming webhook on `/api/v1/subscriptions/webhook` is cryptographically validated against `RAZORPAY_WEBHOOK_SECRET` using `hmac.compare_digest()`.
- **Replay Attack Defense**: Evaluates `payload.payment_id` against previously processed transactions. Duplicate webhooks return `400 Bad Request` and increment the replay security metric.
- **Client Privilege Isolation**: Frontend requests cannot mark subscriptions as active without a valid, signed backend webhook from Razorpay.

---

## 2. Test Verification Matrix

| Scenario | Payload | Expected Outcome | Verification |
|---|---|---|---|
| Valid Webhook | Correct HMAC signature | Subscription activated (Fan Pass) | **PASS** |
| Invalid Signature | Tampered signature header | `400 Bad Request` ("Invalid signature") | **PASS** |
| Webhook Replay | Duplicate `payment_id` | `400 Bad Request` ("Replay detected") | **PASS** |
| Unauthorized Plan Update | User without active payment | `403 Forbidden` | **PASS** |

---

## 3. Test Traceability

- Automated in [`backend/tests/test_phase3_security_hardening.py`](file:///E:/per_char/backend/tests/test_phase3_security_hardening.py) and [`backend/tests/test_end_to_end_journeys.py`](file:///E:/per_char/backend/tests/test_end_to_end_journeys.py).
