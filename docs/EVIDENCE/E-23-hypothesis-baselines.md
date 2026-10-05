# EVIDENCE RECORD: E-23 — Hypothesis Baselines Instrumentation & Query Execution

- **Claim**: Event instrumentation for telemetry (`impression`, `share`, `follow`, `interaction_start`, `meaningful_interaction`, `return_d1/d7/d30`, `variant_id`) is persisted via database schema and all 6 core hypotheses (H1–H6) execute with deterministic measurement.
- **Verification Date**: 2026-10-05T05:02:05.853327+00:00
- **Git Commit**: `a33b913`
- **Exact Command**: `$env:PYTHONPATH="."; .venv\Scripts\python.exe backend/scripts/query_hypotheses_h1_h6.py`
- **Verdict**: **PASSED (All 6 Hypotheses Instrumented & Measured)**

## 1. Verbatim Query Output
```text
H1: Organic Shareability: 10.0% (Threshold: 5.0%) -> PASS
H2: Meaningful Retention (WMCR): 25.93% (Threshold: 25.0%) -> PASS
H3: Character Recognizability A/B: 92.5% (Threshold: 80.0%) -> PASS
H4: Monetization / Willingness to Pay: 11.11% (Threshold: 2.0%) -> PASS
H5: Safety & Injection Immunity: 0.0% (Threshold: 0.1%) -> PASS
H6: Controlled Autonomy Gate: 100.0% (Threshold: 95.0%) -> PASS
```

## 2. Table Schema Parity
- Table `interaction_events` added via Alembic migration `8d239501f22b`.
- Indexing applied on `event_type`, `variant_id`, and `created_at`.
