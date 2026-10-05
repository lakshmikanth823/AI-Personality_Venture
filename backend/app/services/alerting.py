"""
backend/app/services/alerting.py
Operational Alerting Engine for Kalyan AI Platform.
Dispatches critical operational, security, safety, and business metric alerts
to Slack Webhooks and Email (SMTP).
"""

import logging
import json
from typing import Dict, Any, Optional
import httpx
from backend.app.core.config import settings

logger = logging.getLogger("kalyan.alerting")

LEVEL_COLORS = {
    "INFO": "#2eb886",
    "WARNING": "#daa038",
    "CRITICAL": "#a30200",
    "SECURITY": "#7b0099"
}

class SlackWebhookDispatcher:
    """
    Dispatches rich JSON notification payloads to configured Slack incoming webhooks.
    """
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.SLACK_WEBHOOK_URL

    async def send_slack_alert(
        self,
        title: str,
        message: str,
        level: str = "WARNING",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        color = LEVEL_COLORS.get(level.upper(), "#daa038")
        payload = {
            "text": f"[{level.upper()}] {title}",
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in (metadata or {}).items()
                    ],
                    "footer": f"Kalyan AI Platform — {getattr(settings, 'APP_ENV', 'staging')}"
                }
            ]
        }

        if not self.webhook_url:
            logger.info(f"[SLACK ALERT MOCK] Level={level} | Title={title} | Msg={message}")
            return {"dispatched": True, "channel": "slack", "mocked": True, "payload": payload}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(self.webhook_url, json=payload)
                return {
                    "dispatched": res.status_code == 200,
                    "channel": "slack",
                    "status_code": res.status_code,
                    "payload": payload
                }
        except Exception as e:
            logger.error(f"Failed to post Slack alert: {e}")
            return {"dispatched": False, "channel": "slack", "error": str(e), "payload": payload}

class EmailSMTPDispatcher:
    """
    Dispatches operational alerts to on-call engineering / ops mailboxes.
    """
    def __init__(self, smtp_host: Optional[str] = None, smtp_port: Optional[int] = None):
        self.smtp_host = smtp_host or settings.SMTP_HOST
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.recipient = settings.ALERT_EMAIL_RECIPIENT

    async def send_email_alert(
        self,
        subject: str,
        body: str,
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        target = recipient or self.recipient
        if not self.smtp_host:
            logger.info(f"[EMAIL ALERT MOCK] To={target} | Subject={subject} | Body={body[:80]}...")
            return {"dispatched": True, "channel": "email", "mocked": True, "recipient": target}

        # Real SMTP dispatch if host is configured
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = "no-reply-alerts@kalyan-ai.internal"
            msg["To"] = target

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=5) as server:
                server.send_message(msg)
            return {"dispatched": True, "channel": "email", "recipient": target}
        except Exception as e:
            logger.error(f"Failed to dispatch email alert: {e}")
            return {"dispatched": False, "channel": "email", "error": str(e), "recipient": target}

async def dispatch_operational_alert(
    alert_type: str,
    details: Dict[str, Any],
    level: str = "WARNING"
) -> Dict[str, Any]:
    """
    Unified entry point for sending operational alerts across all notification channels.
    """
    title = f"Alert: {alert_type}"
    message = details.get("description", f"Metric threshold breach detected on {alert_type}.")

    slack_disp = SlackWebhookDispatcher()
    email_disp = EmailSMTPDispatcher()

    slack_res = await slack_disp.send_slack_alert(
        title=title,
        message=message,
        level=level,
        metadata=details
    )

    email_body = f"Alert: {title}\nLevel: {level}\n\nDetails:\n" + "\n".join(
        f"- {k}: {v}" for k, v in details.items()
    )
    email_res = await email_disp.send_email_alert(
        subject=f"[{level}] {title}",
        body=email_body
    )

    return {
        "alert_type": alert_type,
        "level": level,
        "slack": slack_res,
        "email": email_res
    }
