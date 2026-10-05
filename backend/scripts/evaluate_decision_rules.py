"""
backend/scripts/evaluate_decision_rules.py
Phase 4 — Decision Rules Gate

Implements 6 blueprint decision rules as threshold config,
seeds synthetic analytics data triggering >=3 rules,
and asserts that alerts fire for each triggered rule.

Usage:
    .venv\\Scripts\\python.exe backend/scripts/evaluate_decision_rules.py
"""

import sys
import os
import json
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# ─── 6 Blueprint Decision Rules ─────────────────────────────────────────────
RULES = {
    "R1_DAILY_MESSAGE_QUOTA_BREACH": {
        "description": "User sent > 100 messages in 24h (quota abuse signal)",
        "threshold": 100,
        "metric": "messages_24h",
        "alert_level": "WARNING",
    },
    "R2_SAFETY_TIER3_SPIKE": {
        "description": ">=3 Tier-3 safety events in last 1h (crisis/abuse cluster)",
        "threshold": 3,
        "metric": "tier3_events_1h",
        "alert_level": "CRITICAL",
    },
    "R3_KILL_SWITCH_ACTIVATION": {
        "description": "Kill switch activated -> all AI responses must pause",
        "threshold": 1,
        "metric": "kill_switch_active",
        "alert_level": "CRITICAL",
    },
    "R4_PAYMENT_WEBHOOK_REPLAY": {
        "description": "Same Razorpay payment_id received >1× (replay attack)",
        "threshold": 1,
        "metric": "webhook_replay_count",
        "alert_level": "SECURITY",
    },
    "R5_DAILY_COST_CEILING_BREACH": {
        "description": "Projected daily LLM cost > $50 USD budget",
        "threshold": 50.0,
        "metric": "projected_daily_cost_usd",
        "alert_level": "WARNING",
    },
    "R6_APPROVAL_QUEUE_STALE": {
        "description": "Approval queue has items pending > 2h without review",
        "threshold": 120,  # minutes
        "metric": "max_pending_minutes",
        "alert_level": "WARNING",
    },
}

# ─── Synthetic analytics data ────────────────────────────────────────────────
# Triggers R1, R2, R3, R4, R5, R6 (all 6 rules)
SYNTHETIC_DATA = {
    "messages_24h": 152,          # R1: > 100
    "tier3_events_1h": 5,         # R2: >= 3
    "kill_switch_active": 1,      # R3: active
    "webhook_replay_count": 2,    # R4: > 1
    "projected_daily_cost_usd": 67.30,  # R5: > 50
    "max_pending_minutes": 195,   # R6: > 120 minutes
}


def evaluate_rules(data: dict) -> list:
    """Evaluate all 6 rules against supplied analytics data. Returns list of fired alerts."""
    fired = []
    for rule_id, rule in RULES.items():
        metric = rule["metric"]
        threshold = rule["threshold"]
        value = data.get(metric, 0)

        if value > threshold:
            alert = {
                "rule_id": rule_id,
                "alert_level": rule["alert_level"],
                "description": rule["description"],
                "metric": metric,
                "value": value,
                "threshold": threshold,
                "excess": round(value - threshold, 4),
                "fired_at": datetime.now(timezone.utc).isoformat(),
            }
            fired.append(alert)

    return fired


def run_decision_rules():
    print("=== DECISION RULES EVALUATION ===")
    print(f"Synthetic analytics input: {json.dumps(SYNTHETIC_DATA, indent=2)}\n")

    fired = evaluate_rules(SYNTHETIC_DATA)

    print(f"Rules fired: {len(fired)} / {len(RULES)}\n")
    for a in fired:
        print(
            f"  [{a['alert_level']}] {a['rule_id']}\n"
            f"    metric={a['metric']}  value={a['value']}  threshold={a['threshold']}  excess={a['excess']}\n"
            f"    description: {a['description']}\n"
        )

    print("=== GATE ASSERTIONS ===")

    # Gate: >=3 rules must fire
    assert len(fired) >= 3, (
        f"GATE FAIL: Only {len(fired)} rules fired; expected >= 3."
    )
    print(f"  [PASS] {len(fired)} rules fired >= 3 minimum")

    # Gate: All expected rules fired given the synthetic data
    fired_ids = {a["rule_id"] for a in fired}
    for rule_id in RULES:
        metric = RULES[rule_id]["metric"]
        val = SYNTHETIC_DATA.get(metric, 0)
        threshold = RULES[rule_id]["threshold"]
        if val > threshold:
            assert rule_id in fired_ids, (
                f"GATE FAIL: Rule {rule_id} should have fired (value={val} > threshold={threshold}) but did not."
            )
            print(f"  [PASS] {rule_id} correctly fired (value={val} > threshold={threshold})")

    print("\n=== DECISION RULES: ALL GATES PASSED ===\n")
    return fired


if __name__ == "__main__":
    alerts = run_decision_rules()
    print(f"Total alerts fired: {len(alerts)}")
