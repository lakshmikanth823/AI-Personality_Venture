import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

# PII Scrubbing Patterns
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
RE_PHONE_IN = re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}\b")
RE_KEY_PAIR = re.compile(r"""(?i)(password|secret|token|api_key|access_token|authorization)\s*[:=]\s*['"]?([a-zA-Z0-9_.\-~+/=]{6,})['"]?""")

def scrub_sensitive_data(text: str) -> str:
    """Scrub PII (emails, Indian phone numbers) and credentials from log messages."""
    if not isinstance(text, str):
        return text
    text = RE_EMAIL.sub("[REDACTED_EMAIL]", text)
    text = RE_PHONE_IN.sub("[REDACTED_PHONE]", text)
    text = RE_KEY_PAIR.sub(r'\1="[REDACTED_SECRET]"', text)
    return text

class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects with UTC timestamp and context propagation."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": scrub_sensitive_data(record.getMessage()),
        }

        # Propagate request context if present
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "client_ip"):
            log_obj["client_ip"] = record.client_ip
        if hasattr(record, "endpoint"):
            log_obj["endpoint"] = record.endpoint
        if hasattr(record, "cost_usd"):
            log_obj["cost_usd"] = record.cost_usd

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

def setup_structured_logging():
    """Initializes root logger to use JSON formatting."""
    root_logger = logging.getLogger()
    # Remove existing handlers
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
