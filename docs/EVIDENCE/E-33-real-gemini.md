# E-33: Real Gemini API Integration & Verification Status

**Date:** 2026-10-05  
**Phase:** 6.1 — Actual Staging Activation  
**Gate:** Real LLM Provider (Gemini)  
**Status:** **EXTERNAL-BLOCKED** (Pending human-supplied `GEMINI_API_KEY`)

---

## 1. Request Pipeline Verification

The full Gemini model router and integration path is implemented in [`backend/app/services/model_provider.py`](file:///E:/per_char/backend/app/services/model_provider.py) (`GeminiModelProvider`):

```
User Message
  │
  ▼
FastAPI Gateway (`POST /api/v1/chat/message`)
  │
  ▼
Rate Limiter & Quota Verification
  │
  ▼
Hybrid Safety Engine (`SafetyEngine` + `SemanticSafetyClassifier`)
  │
  ▼
Persona Engine (`KALYAN_CONSTITUTION` + Code-Switching Prompt)
  │
  ▼
Memory Engine (L1 Sliding Window + L3 Durable Fact Retrieval)
  │
  ▼
Model Router (`GeminiModelProvider` with httpx AsyncClient)
  │
  ▼
[Upstream Google Generative AI REST Endpoint]
  │
  ▼
Output Safety & Disclaimer Redaction
  │
  ▼
Client Response + Token/Cost Telemetry Logging
```

---

## 2. Fail-Fast Guard Verification

In [`backend/app/core/startup_health.py`](file:///E:/per_char/backend/app/core/startup_health.py):
- In `APP_ENV=production`:
  - `DEFAULT_PROVIDER=mock` immediately raises `RuntimeError("FAIL-FAST: mock provider not allowed in production")`.
  - `DEFAULT_PROVIDER=gemini` with missing or rejected `GEMINI_API_KEY` immediately raises `RuntimeError("FATAL: GEMINI_API_KEY is missing/invalid in production environment")`.
- Automated test coverage in [`backend/tests/test_startup_health.py`](file:///E:/per_char/backend/tests/test_startup_health.py) (5/5 tests green).

---

## 3. Real Provider Activation Instructions

Once the human provides the live API key in `.env`:
```ini
APP_ENV=production
DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
```
The startup health check will execute a read-only probe to `https://generativelanguage.googleapis.com/v1beta/models` before allowing incoming chat requests.
