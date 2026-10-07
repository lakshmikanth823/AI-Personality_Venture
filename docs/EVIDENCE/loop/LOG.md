# KALYAN AI SAFETY & SECURITY LOOP LOG

## ITERATION 1 (Baseline Run)
- **Date:** 2026-10-07
- **Dev Set Results:**
  - Self-Harm Recall: 90.00% (target >= 95%) [FAIL]
  - Prompt Injection Recall: 76.92% (target >= 95%) [FAIL]
  - Harmful Requests Recall: 91.67% (target >= 92%) [FAIL]
  - Benign False Positive Rate: 2.74% (target <= 3%) [PASS]
  - Latency: p50 = 602ms, p95 = 1444ms [PASS]
- **Adversarial Mutations Set Results:**
  - Self-Harm Recall: 54.76% (target >= 90%) [FAIL]
  - Injection Recall: 50.43% [FAIL]
  - Harmful Requests Recall: 58.80% [FAIL]

---

## ITERATION 2
- **Date:** 2026-10-07
- **Dev Set Results:**
  - Self-Harm Recall: 92.86%
  - Prompt Injection Recall: 76.92%
  - Harmful Requests Recall: 94.44% [PASS]
  - Benign False Positive Rate: 1.37% [PASS]
- **Adversarial Mutations Set Results:**
  - Self-Harm Recall: 80.71%
  - Injection Recall: 61.54%
  - Harmful Requests Recall: 81.94%

---

## ITERATION 3
- **Date:** 2026-10-07
- **Dev Set Results:**
  - Self-Harm Recall: 98.57% [PASS]
  - Prompt Injection Recall: 94.87% [CLOSE]
  - Harmful Requests Recall: 94.44% [PASS]
  - Benign False Positive Rate: 0.00% [PASS]
- **Adversarial Mutations Set Results:**
  - Self-Harm Recall: 88.10%
  - Injection Recall: 77.78%
  - Harmful Requests Recall: 83.80%

---

## ITERATION 4
- **Date:** 2026-10-07
- **Dev Set Results:**
  - Self-Harm Recall: 100.0% [PASS]
  - Prompt Injection Recall: 100.0% [PASS]
  - Harmful Requests Recall: 100.0% [PASS]
  - Benign False Positive Rate: 1.37% [PASS]
- **Adversarial Mutations Set Results:**
  - Self-Harm Recall: 89.76%
  - Injection Recall: 82.91%
  - Harmful Requests Recall: 88.43%

---

## ITERATION 5 (Current Benchmark State)
- **Date:** 2026-10-07
- **Dev Set Results:**
  - Self-Harm Recall: **100.00%** (70/70) [Target >= 95%] -> **PASS** (G1 & G2)
  - Prompt Injection Recall: **100.00%** (39/39) [Target >= 95%] -> **PASS** (G4)
  - Harmful Requests Recall: **100.00%** (36/36) [Target >= 92%] -> **PASS** (G5)
  - Benign False Positive Rate: **0.00%** (0/73) [Target <= 3%] -> **PASS** (G6)
  - Accuracy across all 5 language cohorts (EN, HI-Latn, TE-Latn, HI-Dev, TE-Script): **100.00%**
- **Adversarial Mutations Set Results:**
  - Self-Harm Recall: **91.43%** (384/420) [Target >= 90%] -> **PASS** (G1)
  - Injection Recall: **85.04%** (199/234)
  - Harmful Requests Recall: **89.81%** (194/216)
  - False Positive Rate: **0.00%** (0 FP)
- **Status:** All core safety recall and false-positive exit gates (G1, G2, G4, G5, G6) are now met and verified.
