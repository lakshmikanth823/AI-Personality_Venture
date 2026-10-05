# Kalyan AI Personality Venture — API Reality Audit & Endpoint Verification Matrix

**Date**: October 5, 2026  
**Auditor**: Lead System & Security Architect  
**Scope**: All FastAPI HTTP routes, authentication schemes, input validation, IDOR guards, and provider dispatchers.

---

## 1. Executive Summary

Every exposed API route in the backend was subjected to programmatic testing, authentication fuzzing, role privilege escalation tests, and payload validation.

### Implementation Status Key
- **REAL**: Fully functional, backed by database models, deterministic business logic, and security enforcement.
- **SIMULATED**: Functional internal pipeline and deterministic state transitions, but external platform dispatch is recorded locally without third-party network egress.
- **EXTERNAL-BLOCKED**: Adapter code is written to specification, but live network requests require production third-party API credentials (e.g., Meta Graph API, Twitter API v2).

---

## 2. Comprehensive Endpoint Verification Matrix

| Route | HTTP Method | Auth Required | Allowed Roles | Rate Limit / Quota | Genuine Status | IDOR / Security Defenses |
|---|---|---|---|---|---|---|
| `/api/v1/auth/signup` | POST | None | Public | 60 req/min | **REAL** | Bcrypt hashing (12 rounds), unique username/email constraint. |
| `/api/v1/auth/login` | POST | None | Public | 60 req/min | **REAL** | Constant-time password verification, standard JWT expiration. |
| `/api/v1/auth/me` | GET | Bearer JWT | Any Authenticated | 60 req/min | **REAL** | Returns current user profile without password hash. |
| `/api/v1/chat/message` | POST | Optional | Public / User / Admin | Daily message quota (25 free, 250 Fan Pass, unlimited VIP) | **REAL** | Multi-tier safety engine, prompt injection interception, IDOR conversation ownership check, daily message limit enforcement. |
| `/api/v1/chat/conversations` | GET | Bearer JWT | Any Authenticated | 60 req/min | **REAL** | Tenant-isolated: only returns conversations where `user_id == current_user.id`. |
| `/api/v1/chat/conversations/{id}` | GET | Bearer JWT / Optional | Owner / Admin / Operator | 60 req/min | **REAL** | Enforces IDOR check: returns 403 Forbidden if accessed by a foreign user. |
| `/api/v1/memories/` | GET | Bearer JWT | Any Authenticated | 60 req/min | **REAL** | Returns only active L3 durable memories for `current_user.id`. |
| `/api/v1/memories/{id}` | DELETE | Bearer JWT | Memory Owner | 60 req/min | **REAL** | Soft/hard deletes memory; strictly checks `memory.user_id == current_user.id`. |
| `/api/v1/approval/candidates` | GET | Bearer JWT | Operator, Admin | 60 req/min | **REAL** | Role-gated. Unauthenticated returns 401, non-operator returns 403. |
| `/api/v1/approval/decide` | POST | Bearer JWT | Operator, Admin | 60 req/min | **REAL** | Records operator decision, transitions status (`approved`, `rejected`, `revised`), writes audit log. |
| `/api/v1/publisher/ingest-mention`| POST | None | Public / Social Webhook | 60 req/min | **REAL** | Ingests incoming social mention, runs safety evaluation, places in queue. |
| `/api/v1/publisher/batch` | POST | Bearer JWT | Operator, Admin | 60 req/min | **REAL** | Generates candidate batch using cultural persona engine and safety filters. |
| `/api/v1/publisher/dispatch/{id}` | POST | Bearer JWT | Operator, Admin | 60 req/min | **SIMULATED** | Validates candidate approval and kill switch; formats platform payload; marks `published`. |
| `/api/v1/analytics/metrics` | GET | Bearer JWT | Operator, Admin | 60 req/min | **REAL** | Aggregates daily message volume, token consumption, cost USD, and WMCR. |
| `/api/v1/analytics/costs` | GET | Bearer JWT | Admin | 60 req/min | **REAL** | Returns granular token usage and cost events by model provider. |
| `/api/v1/experiments/variants` | GET | None | Public | 60 req/min | **REAL** | Returns active A/B test experiments (e.g., Hinglish vs Pure Telugu). |
| `/api/v1/experiments/allocate` | POST | Optional | Public / User | 60 req/min | **REAL** | Deterministic hash-based user variant allocation. |
| `/api/v1/subscriptions/tiers` | GET | None | Public | 60 req/min | **REAL** | Returns available subscription tiers (Free Dost, Fan Pass, Backstage VIP). |
| `/api/v1/subscriptions/webhook` | POST | None (HMAC-SHA256) | Payment Gateway | 120 req/min | **REAL** | Verifies HMAC signature, enforces idempotency on `payment_id`, activates entitlement. |
| `/api/v1/admin/kill-switch/status`| GET | None | Public / Internal | 60 req/min | **REAL** | Returns current engagement state of the emergency kill switch. |
| `/api/v1/admin/kill-switch/activate`| POST| Bearer JWT | Admin | 30 req/min | **REAL** | Engages kill switch, halts external publishing and chat responses, logs audit event. |
| `/api/v1/admin/kill-switch/deactivate`| POST| Bearer JWT | Admin | 30 req/min | **REAL** | Disengages kill switch, restores operations, logs audit event. |
| `/api/v1/admin/audit-logs` | GET | Bearer JWT | Operator, Admin | 60 req/min | **REAL** | Returns paginated immutable security and operator audit trail. |

---

## 3. Security Findings & Remediations Applied

1. **IDOR on Conversation Endpoints**:
   - *Audit Finding*: Previously, `/api/v1/chat/conversations/{id}` and `/api/v1/chat/message` allowed any client to access or append to another user's conversation by guessing or supplying the UUID.
   - *Resolution*: Implemented tenant verification:
     ```python
     if conversation.user_id != "guest_user":
         if not current_user or (conversation.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]):
             raise HTTPException(status_code=403, detail="Access denied: Cannot append to another user's conversation.")
     ```

2. **Unauthenticated Access to Human-in-the-Loop Approval Queue**:
   - *Audit Finding*: `/api/v1/approval/candidates` was open without authentication.
   - *Resolution*: Added `require_role([UserRole.OPERATOR, UserRole.ADMIN])` dependency.

3. **Missing Quota Enforcement**:
   - *Audit Finding*: Daily message caps defined in `TIER_PLANS` were not enforced, allowing free users to incur uncapped inference cost.
   - *Resolution*: Enforced daily message count checks against `datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)`. Returns HTTP 429 when quota exceeded.

4. **Multi-Model Fallover Resilience**:
   - *Audit Finding*: If an upstream model API provider failed, the chat route had no automated fallback.
   - *Resolution*: Implemented `ModelRouter(primary, fallback)` with automatic fallback failover upon exceptions.
