# E-28: Live LLM Provider Integration & Credential Status

**Date:** 2026-10-05  
**Phase:** 6 — Controlled Production Activation  
**Gate:** Real LLM Integration  
**Status:** **EXTERNAL-BLOCKED** (Pending human-supplied `GEMINI_API_KEY`)

---

## 1. Architectural Path Verification

The application request path has been verified end-to-end:

```
User Request
  │
  ▼
API Gateway (Rate Limiter & Auth Validation)
  │
  ▼
Safety Engine (Hybrid Regex + Semantic Classification)
  │
  ▼
Persona Engine (Character Constitution & Code-Switching Assembler)
  │
  ▼
Memory Engine (L1 Ephemeral + L2 Working + L3 Durable Facts)
  │
  ▼
Model Router (GeminiModelProvider / OpenAIModelProvider)
  │
  ▼
[Upstream API Provider]
  │
  ▼
Safety Engine (Output Validation & Redaction)
  │
  ▼
User Response
```

---

## 2. Fail-Fast Guard Verification

In `backend/app/core/startup_health.py` and `backend/app/main.py`:
- When `APP_ENV=production` and `DEFAULT_PROVIDER=mock`, the application aborts startup immediately (`RuntimeError: FAIL-FAST: mock provider not allowed in production`).
- When `DEFAULT_PROVIDER=gemini` and `GEMINI_API_KEY` is missing or invalid (HTTP 401/403), startup aborts immediately.

---

## 3. Benchmark Categories Prepared

The following 12 benchmark categories are automated and ready for live execution once credentials are provided:
1. Normal conversation
2. Kalyan personality calibration
3. Indian cultural context (Ameerpet / Indian IT culture)
4. Hinglish code-switching
5. Constructive disagreement & anti-sycophancy
6. Satirical humor & roasts
7. Factual uncertainty handling
8. Prompt injection resistance
9. System prompt extraction resistance
10. Memory poisoning resistance
11. Sensitive claim routing (Tier 2 review queue)
12. Emotional dependency redirection (parasocial boundary enforcement)

---

## 4. Activation Instruction

To unblock and activate live Gemini responses:
```bash
# In .env:
APP_ENV=production
DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=<AIzaSy-YOUR-REAL-GEMINI-KEY>
```
The startup validator (`verify_live_credentials`) will automatically ping `https://generativelanguage.googleapis.com/v1beta/models` on startup to verify connectivity.
