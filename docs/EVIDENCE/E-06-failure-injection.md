# Evidence Record E-06: Failure-Injection Matrix & Chaos Recovery

- **Requirement Reference**: G-06 (Failure-Injection Matrix & Chaos Recovery)
- **UTC Timestamp**: 2026-10-05T04:28:00Z
- **Git Commit Hash**: `6bd183c972b7954896a8e852e7e3a98521c65048`
- **Status**: CLOSED

---

## 1. Specification & Protocol

The system was audited against 6 high-severity failure and chaos vectors to verify that failures degrade gracefully without crashing backend processes, corrupting durable database state, or double-crediting user entitlements:
1. **LLM Provider Timeout (HTTP 504 / `asyncio.TimeoutError`)**: Simulated network lag; router must fail over dynamically to local deterministic fallback.
2. **Provider Rate Limiting (HTTP 429)**: Upstream quota exhaustion; router intercepts and dispatches fallback response.
3. **Provider 500 Internal Server Error**: Remote unhandled crash; fallback serves valid response.
4. **Database Transaction / Constraint Failure**: Collision on persistent records; session cleanly rolls back and accepts subsequent queries without orphaned locks.
5. **Malformed JSON Payloads**: Truncated or corrupt bytes in external webhook endpoints; returns HTTP 400 with descriptive error without server panic.
6. **Payment Webhook Replay & Duplicate Attack**: Replaying identical signed Razorpay webhooks multiple times; verifies that signature is verified and duplicate delivery is acknowledged (200 OK) without double-charging or duplicating subscription duration.

---

## 2. Test Execution & Verbatim Evidence

- **Command**:
  ```powershell
  $env:PYTHONPATH="."; .venv\Scripts\pytest.exe -v backend/tests/test_failure_injection.py
  ```
- **Verbatim Stdout**:
  ```
  ============================= test session starts =============================
  platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- E:\per_char\.venv\Scripts\python.exe
  cachedir: .pytest_cache
  rootdir: E:\per_char
  configfile: pytest.ini
  plugins: anyio-4.15.1, asyncio-1.4.0, base-url-2.1.0, playwright-0.9.0
  asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
  collecting ... collected 6 items

  backend/tests/test_failure_injection.py::test_failure_injection_provider_timeout_failover PASSED [ 16%]
  backend/tests/test_failure_injection.py::test_failure_injection_provider_429_failover PASSED [ 33%]
  backend/tests/test_failure_injection.py::test_failure_injection_provider_500_failover PASSED [ 50%]
  backend/tests/test_failure_injection.py::test_failure_injection_database_operational_recovery PASSED [ 66%]
  backend/tests/test_failure_injection.py::test_failure_injection_malformed_json_payload PASSED [ 83%]
  backend/tests/test_failure_injection.py::test_failure_injection_signed_payment_webhook_replay PASSED [100%]

  ======================== 6 passed, 1 warning in 0.29s =========================
  ```
- **Exit Code**: 0

---

## 3. Failure Mode Outcomes

| Test ID | Injected Failure | Behavior / Recovery | Outcome |
|---|---|---|---|
| 1 | HTTP 504 / Timeout | Automatic failover to local model fallback | PASSED |
| 2 | HTTP 429 Rate Limit | Automatic failover to local model fallback | PASSED |
| 3 | HTTP 500 Server Error | Intercepted by router, served fallback | PASSED |
| 4 | DB Integrity Collision | Session rollback, subsequent queries succeed | PASSED |
| 5 | Malformed JSON Payload | HTTP 400 Bad Request, zero uncaught exception | PASSED |
| 6 | Webhook Replay Attack | HMAC signature checked, duplicate idempotent skip | PASSED |
