from typing import Dict, List
import time
from sqlalchemy.orm import Session
from backend.app.models.content import ContentCandidate
from backend.app.models.safety import KillSwitchState

class PrometheusMetricsRegistry:
    """
    In-memory Prometheus metrics registry for Kalyan AI Personality platform.
    Produces standard Prometheus text exposition format (0.0.4).
    """
    def __init__(self):
        self.request_count: Dict[str, int] = {}
        self.total_tokens_input: int = 0
        self.total_tokens_output: int = 0
        self.total_cost_usd: float = 0.0
        self.request_latencies: List[float] = []

    def record_request(self, endpoint: str, status_code: int, duration_sec: float):
        key = f'{endpoint},{status_code}'
        self.request_count[key] = self.request_count.get(key, 0) + 1
        self.request_latencies.append(duration_sec)
        # Keep last 1,000 latency measurements in memory
        if len(self.request_latencies) > 1000:
            self.request_latencies.pop(0)

    def record_tokens(self, tokens_in: int, tokens_out: int, cost: float):
        self.total_tokens_input += tokens_in
        self.total_tokens_output += tokens_out
        self.total_cost_usd += cost

    def render_prometheus(self, db: Session = None) -> str:
        lines = []

        # 1. HTTP Requests Total
        lines.append("# HELP http_requests_total Total number of HTTP requests processed")
        lines.append("# TYPE http_requests_total counter")
        for key, count in self.request_count.items():
            endpoint, status_code = key.split(",")
            lines.append(f'http_requests_total{{endpoint="{endpoint}",status="{status_code}"}} {count}')

        # 2. LLM Tokens
        lines.append("# HELP llm_tokens_total Total LLM tokens processed")
        lines.append("# TYPE llm_tokens_total counter")
        lines.append(f'llm_tokens_total{{direction="input"}} {self.total_tokens_input}')
        lines.append(f'llm_tokens_total{{direction="output"}} {self.total_tokens_output}')

        # 3. Estimated Cost USD
        lines.append("# HELP estimated_cost_usd_total Accumulated cost in USD from LLM inferences")
        lines.append("# TYPE estimated_cost_usd_total counter")
        lines.append(f'estimated_cost_usd_total {self.total_cost_usd:.6f}')

        # 4. Latency Summary
        if self.request_latencies:
            sorted_lat = sorted(self.request_latencies)
            p50 = sorted_lat[int(len(sorted_lat) * 0.5)]
            p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
            p99 = sorted_lat[int(len(sorted_lat) * 0.99)]
            lines.append("# HELP http_request_duration_seconds Latency summary")
            lines.append("# TYPE http_request_duration_seconds summary")
            lines.append(f'http_request_duration_seconds{{quantile="0.5"}} {p50:.4f}')
            lines.append(f'http_request_duration_seconds{{quantile="0.95"}} {p95:.4f}')
            lines.append(f'http_request_duration_seconds{{quantile="0.99"}} {p99:.4f}')

        # 5. Operational Queue Depth & Kill Switch
        if db:
            try:
                pending_count = db.query(ContentCandidate).filter(ContentCandidate.status == "pending_approval").count()
                lines.append("# HELP content_approval_queue_depth Pending content candidate approval count")
                lines.append("# TYPE content_approval_queue_depth gauge")
                lines.append(f"content_approval_queue_depth {pending_count}")

                ks = db.query(KillSwitchState).first()
                ks_val = 1 if (ks and ks.is_active) else 0
                lines.append("# HELP kill_switch_active Current global emergency kill-switch state (1=active, 0=inactive)")
                lines.append("# TYPE kill_switch_active gauge")
                lines.append(f"kill_switch_active {ks_val}")
            except Exception:
                pass

        return "\n".join(lines) + "\n"

metrics_registry = PrometheusMetricsRegistry()
