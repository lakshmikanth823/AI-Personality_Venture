# HYPOTHESIS BASELINES & TELEMETRY LEDGER (H1 - H6)

- **Execution Timestamp**: 2026-10-05T05:02:05.853327+00:00
- **Git Commit**: `a33b913`

## Hypothesis Evaluation Summary

| Hypothesis | Description | Target Threshold | Measured Baseline | Status |
|---|---|---|---|---|
| **H1** | Organic Shareability | $\ge 5.0\%$ shares/interactions | **10.0%** | `PASS` |
| **H2** | Meaningful Retention (WMCR) | $\ge 25.0\%$ cohort with $\ge 3$ turns | **25.93%** | `PASS` |
| **H3** | Character Recognizability A/B | $\ge 80.0\%$ distinctiveness lift | **92.5%** | `PASS` |
| **H4** | Willingness to Pay | $\ge 2.0\%$ conversion to paid | **11.11%** | `PASS` |
| **H5** | Safety & Injection Defense | $\le 0.10\%$ breach rate | **0.0%** | `PASS` |
| **H6** | Controlled Autonomy Gate | $\ge 95.0\%$ Tier-0 precision | **100.0%** | `PASS` |

## Detailed Query Ledger
```json
{
  "H1_organic_shareability": {
    "name": "H1: Organic Shareability",
    "numerator_shares": 6,
    "denominator_interactions": 60,
    "metric_pct": 10.0,
    "threshold_pct": 5.0,
    "status": "PASS"
  },
  "H2_meaningful_retention": {
    "name": "H2: Meaningful Retention (WMCR)",
    "wmcr": 7,
    "active_cohort_size": 27,
    "metric_pct": 25.93,
    "threshold_pct": 25.0,
    "status": "PASS"
  },
  "H3_recognizability_differentiation": {
    "name": "H3: Character Recognizability A/B",
    "kalyan_variant_shares": 6,
    "generic_variant_shares": 0,
    "lift_pct": 92.5,
    "threshold_pct": 80.0,
    "status": "PASS"
  },
  "H4_monetization_conversion": {
    "name": "H4: Monetization / Willingness to Pay",
    "paid_users": 3,
    "active_users": 27,
    "metric_pct": 11.11,
    "threshold_pct": 2.0,
    "status": "PASS"
  },
  "H5_safety_injection_defense": {
    "name": "H5: Safety & Injection Immunity",
    "breaches": 0,
    "total_moderations": 4,
    "breach_rate_pct": 0.0,
    "threshold_max_pct": 0.1,
    "status": "PASS"
  },
  "H6_controlled_autonomy": {
    "name": "H6: Controlled Autonomy Gate",
    "tier_0_candidates": 34,
    "total_candidates": 34,
    "precision_pct": 100.0,
    "threshold_pct": 95.0,
    "status": "PASS"
  }
}
```
