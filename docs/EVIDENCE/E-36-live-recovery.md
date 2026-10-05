# E-36: Failure Injection, Fallback & Operational Recovery

**Date:** 2026-10-05  
**Phase:** 6.1 — Actual Staging Activation  
**Gate:** Failure Recovery  
**Status:** **PASS**  
**Evidence Command:** `.venv\Scripts\pytest.exe backend/tests/test_failure_injection.py backend/tests/test_kill_switch.py backend/tests/test_operational_drills.py`

---

## 1. Fault Injection Test Matrix

Verified in [`backend/tests/test_failure_injection.py`](file:///E:/per_char/backend/tests/test_failure_injection.py):

| Component Failed | Injected Failure | System Detection & Handling | Recovery Mechanism | Result |
|---|---|---|---|---|
| **Redis Cache / Rate Limiter** | Redis unreachable / socket timeout | Logs warning, catches exception gracefully | Automatic in-memory sliding-window fallback | **PASS** |
| **Database Pool** | Operational error on transaction | Rollback executed, transaction boundary protected | Session close & pool reconnection | **PASS** |
| **Model Provider** | Upstream 503 / network timeout | Model router catches `httpx.RequestError` | Dispatches fallback response / circuit breaker | **PASS** |
| **Kill Switch** | `POST /api/v1/admin/kill-switch/activate` | All inference & outbox dispatch instantly paused | `POST /api/v1/admin/kill-switch/deactivate` unlocks | **PASS** |
| **Daily Cost Budget** | Accumulated inference cost $> \$50.00$ | Free chat rejected with `HTTP 429` | Resets at IST midnight boundary | **PASS** |
| **Corrupt Payload** | Garbage JSON / null bytes / malformed Unicode | Pydantic validation intercept | Returns clean `HTTP 422 Unprocessable Entity` | **PASS** |

---

## 2. Test Traceability

- 6 automated failure injection scenarios passing in [`test_failure_injection.py`](file:///E:/per_char/backend/tests/test_failure_injection.py).
- 3 operational drill scenarios passing in [`test_operational_drills.py`](file:///E:/per_char/backend/tests/test_operational_drills.py).
- 1 kill switch circuit breaker scenario passing in [`test_kill_switch.py`](file:///E:/per_char/backend/tests/test_kill_switch.py).
