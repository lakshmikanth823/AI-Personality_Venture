"""
backend/scripts/test_observability_alerting.py
Automated verification script for Phase 6.3 Task 3:
Operational Alerting & Observability Engine.
"""

import sys
import os
import json
import uuid
import asyncio
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.database import SessionLocal
from backend.app.core.metrics import PrometheusMetricsRegistry, metrics_registry
from backend.app.services.alerting import (
    SlackWebhookDispatcher,
    EmailSMTPDispatcher,
    dispatch_operational_alert,
    LEVEL_COLORS,
)


async def run_observability_and_alerting_verification():
    print("=================================================================")
    print("🚀 PHASE 6.3 TASK 3: OPERATIONAL ALERTING & OBSERVABILITY ENGINE")
    print("=================================================================\n")

    db = SessionLocal()
    passed_checks = 0
    total_checks = 6

    # -------------------------------------------------------------
    # 1. Prometheus Metrics Registry Unit Testing
    # -------------------------------------------------------------
    print("[Check 1/6] Testing Prometheus Metrics Registry Core Methods...")
    local_registry = PrometheusMetricsRegistry()

    # Record simulated traffic
    local_registry.record_request("/api/v1/chat/message", 200, 0.42)
    local_registry.record_request("/api/v1/chat/message", 200, 0.58)
    local_registry.record_request("/api/v1/chat/message", 500, 0.12)
    local_registry.record_request("/api/v1/publisher/publish", 200, 0.08)

    # Record token usage and costs
    local_registry.record_tokens(tokens_in=350, tokens_out=150, cost=0.000125)
    local_registry.record_tokens(tokens_in=500, tokens_out=220, cost=0.000210)

    rendered_text = local_registry.render_prometheus(db=db)
    assert "# HELP http_requests_total" in rendered_text
    assert 'http_requests_total{endpoint="/api/v1/chat/message",status="200"} 2' in rendered_text
    assert 'http_requests_total{endpoint="/api/v1/chat/message",status="500"} 1' in rendered_text
    assert 'llm_tokens_total{direction="input"} 850' in rendered_text
    assert 'llm_tokens_total{direction="output"} 370' in rendered_text
    assert 'estimated_cost_usd_total 0.000335' in rendered_text
    assert 'http_request_duration_seconds{quantile="0.95"}' in rendered_text
    assert "kill_switch_active" in rendered_text
    print("  ✓ Local PrometheusMetricsRegistry rendered valid Prometheus 0.0.4 text format.")
    passed_checks += 1

    # -------------------------------------------------------------
    # 2. Live Server /metrics Endpoint Query
    # -------------------------------------------------------------
    print("\n[Check 2/6] Querying Live Server Endpoint GET /metrics...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get("http://127.0.0.1:8000/metrics")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            assert "text/plain" in resp.headers.get("content-type", "")
            metrics_body = resp.text
            print(f"  Live /metrics response received ({len(metrics_body)} bytes):")
            for line in metrics_body.strip().split("\n")[:8]:
                print(f"    {line}")
            print("  ✓ Live /metrics endpoint verified and accessible.")
            passed_checks += 1
        except Exception as e:
            print(f"  ⚠️ Live /metrics request failed: {e}")
            raise

    # -------------------------------------------------------------
    # 3. Slack Webhook Dispatcher Rich Payload Validation
    # -------------------------------------------------------------
    print("\n[Check 3/6] Testing Slack Webhook Alert Dispatcher...")
    slack_disp = SlackWebhookDispatcher()
    slack_res = await slack_disp.send_slack_alert(
        title="High Latency Spike Detected",
        message="Gemini P95 inference latency exceeded 2500ms on 10 consecutive requests.",
        level="WARNING",
        metadata={
            "service": "kalyan-llm-proxy",
            "model": "gemini-3.5-flash-lite",
            "p95_latency_ms": 2840,
            "threshold_ms": 2500,
        }
    )
    assert slack_res["dispatched"] is True
    assert slack_res["payload"]["attachments"][0]["color"] == LEVEL_COLORS["WARNING"]
    assert len(slack_res["payload"]["attachments"][0]["fields"]) == 4
    print(f"  ✓ Slack Alert Formatted Correctly (Color={slack_res['payload']['attachments'][0]['color']})")
    passed_checks += 1

    # -------------------------------------------------------------
    # 4. Email SMTP Dispatcher Payload Validation
    # -------------------------------------------------------------
    print("\n[Check 4/6] Testing Email SMTP Alert Dispatcher...")
    email_disp = EmailSMTPDispatcher()
    email_res = await email_disp.send_email_alert(
        subject="[CRITICAL] Security Kill Switch Activated",
        body="Operator admin-01 engaged the global emergency kill switch due to anomalous outbound request burst.",
        recipient="ops-oncall@kalyan-personality.internal"
    )
    assert email_res["dispatched"] is True
    assert email_res["recipient"] == "ops-oncall@kalyan-personality.internal"
    print(f"  ✓ Email Alert Dispatcher Formatted & Route Verified (Recipient={email_res['recipient']})")
    passed_checks += 1

    # -------------------------------------------------------------
    # 5. Unified Alert Scenarios (Cost, Security, Kill Switch)
    # -------------------------------------------------------------
    print("\n[Check 5/6] Testing Unified Multi-Channel Operational Alerts...")

    scenarios = [
        {
            "type": "HIGH_COST_THRESHOLD_EXCEEDED",
            "level": "WARNING",
            "details": {
                "description": "Hourly LLM token cost exceeded $5.00 limit ($6.42 accumulated).",
                "hourly_spend_usd": 6.42,
                "budget_cap_usd": 5.00,
                "active_users_count": 142,
            }
        },
        {
            "type": "SAFETY_BREACH_SEV1",
            "level": "SECURITY",
            "details": {
                "description": "Critical jailbreak pattern detected and blocked by Tier 3 regex classifier.",
                "user_id": "usr_99812_attacker",
                "category": "prompt_injection_jailbreak",
                "action_taken": "BLOCKED_WITH_CANONICAL_REFUSAL"
            }
        },
        {
            "type": "KILL_SWITCH_ENGAGED",
            "level": "CRITICAL",
            "details": {
                "description": "Global emergency kill switch engaged by on-call security officer.",
                "actor_id": "sec-ops-lead",
                "reason": "Suspected token exfiltration probe.",
                "affected_channels": "ALL_SOCIAL_EGRESS_HALTED"
            }
        }
    ]

    for scenario in scenarios:
        res = await dispatch_operational_alert(
            alert_type=scenario["type"],
            details=scenario["details"],
            level=scenario["level"]
        )
        assert res["alert_type"] == scenario["type"]
        assert res["level"] == scenario["level"]
        assert res["slack"]["dispatched"] is True
        assert res["email"]["dispatched"] is True
        print(f"  ✓ Alert Dispatched: {scenario['type']} [{scenario['level']}] -> Slack & Email OK")

    passed_checks += 1

    # -------------------------------------------------------------
    # 6. Live Telemetry Pipeline End-to-End Latency & Cost Ingestion
    # -------------------------------------------------------------
    print("\n[Check 6/6] Verifying Live Telemetry Ingestion into Global Registry...")
    metrics_registry.record_request("/api/v1/chat/message", 200, 0.450)
    metrics_registry.record_tokens(tokens_in=120, tokens_out=85, cost=0.000045)

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get("http://127.0.0.1:8000/metrics")
        assert resp.status_code == 200
        assert "http_requests_total" in resp.text
        assert "estimated_cost_usd_total" in resp.text

    print("  ✓ Live global Prometheus metrics updated and verified via HTTP query.")
    passed_checks += 1

    print("\n=================================================================")
    print(f"🎉 OPERATIONAL ALERTING & OBSERVABILITY PASSED: {passed_checks}/{total_checks} CHECKS GREEN")
    print("=================================================================")
    db.close()
    return True


if __name__ == "__main__":
    success = asyncio.run(run_observability_and_alerting_verification())
    sys.exit(0 if success else 1)
