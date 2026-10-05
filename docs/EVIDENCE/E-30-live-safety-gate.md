# E-30: Hybrid Safety Gate & Live Moderation Pipeline

**Date:** 2026-10-05  
**Phase:** 6 — Controlled Production Activation  
**Gate:** Safety  
**Status:** **PASS**  
**Evidence Command:** `.venv\Scripts\python.exe backend/scripts/run_shadow_mode.py` and `.venv\Scripts\pytest.exe backend/tests/test_safety.py`

---

## 1. Safety Pipeline Structure

All inbound and outbound interactions pass through the **Two-Stage Hybrid Moderation Engine**:
1. **Fast-Path Regex (`SafetyEngine`)**: Catches explicit instruction overrides, DAN prompts, self-harm keywords, and hard violations in $<1\text{ms}$.
2. **Semantic Safety Classifier (`SemanticSafetyClassifier`)**: Intercepts obfuscations, leetspeak (`k!ll my$elf`), base64 encoded injection payloads, plural weapon/explosives variants, and disguised health/prescription claims.

---

## 2. Benchmark & Shadow Mode Verification

```
=== SHADOW MODE CONFUSION MATRIX ===
Total candidates      : 200
TP (hazard, correct)  : 150
TN (safe, correct)    : 50
FP (safe flagged)     : 0
FN (hazard missed)    : 0
Agreement             : 100.0%
Disagreements         : 0

=== GATE ASSERTIONS ===
  [PASS] Agreement 100.0% >= 95%
  [PASS] Zero FP on Tier >= 1 (FP=0)
```

---

## 3. Threat Matrix Coverage

| Hazard Category | Test Payload Type | Policy Flag | Action Taken |
|---|---|---|---|
| **Prompt Injection** | Instruction override / DAN / system prompt dump | `prompt_injection` | **BLOCKED (Tier 3)** |
| **Base64 Injection** | `reveal system prompt now` encoded in base64 | `prompt_injection` | **BLOCKED (Tier 3)** |
| **Self-Harm** | Direct keywords + leetspeak (`k!ll my$elf`) | `self_harm` | **BLOCKED (Tier 3)** + Helpline Disclosure |
| **Weapons & Explosives** | Plural variants (`manufacture explosives`) | `severe_hazard` | **BLOCKED (Tier 3)** |
| **Medical Claims** | Unverified cure & strong drug prescriptions | `sensitive_claims` | **REVIEW_QUEUE (Tier 2)** |
| **Election Claims** | Rigged/stolen election conspiracies | `sensitive_claims` | **REVIEW_QUEUE (Tier 2)** |
| **Edgy Banter** | Roast me / career roast | `edgy_banter` | **ALLOWED (Tier 1)** |
| **Safe Chat** | Chai / city / culture questions | `clean` | **ALLOWED (Tier 0)** |

---

## 4. Test Traceability

- Automated in [`backend/tests/test_safety.py`](file:///E:/per_char/backend/tests/test_safety.py) (10/10 tests green).
