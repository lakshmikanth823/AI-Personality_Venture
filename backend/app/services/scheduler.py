import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.content import ContentCandidate, PublishedAction
from backend.app.services.social_gateway import SocialPublisherService, SocialPublishError
from backend.app.services.kill_switch import KillSwitchManager

class ContentSchedulerWorker:
    """
    Background worker that monitors scheduled candidates and auto-publishes
    approved content when due, interlocked strictly with the Global Kill Switch.
    """
    def __init__(self, db: Session):
        self.db = db
        self.publisher = SocialPublisherService(db)
        self.kill_switch = KillSwitchManager(db)

    def process_due_content(self) -> Dict[str, Any]:
        if self.kill_switch.is_kill_switch_active():
            return {
                "status": "halted_by_kill_switch",
                "processed_count": 0,
                "message": "Scheduler execution paused: Emergency Kill Switch is ACTIVE."
            }

        now = datetime.now(timezone.utc)
        # Find candidates that are approved and scheduled for publishing now or in the past
        due_candidates = (
            self.db.query(ContentCandidate)
            .filter(
                ContentCandidate.status == "approved",
                ContentCandidate.scheduled_for != None,
                ContentCandidate.scheduled_for <= now
            )
            .limit(10)
            .all()
        )

        published_ids = []
        errors = []

        for cand in due_candidates:
            try:
                res = self.publisher.publish_candidate(cand.id, operator_id="scheduler_daemon")
                published_ids.append(cand.id)
            except SocialPublishError as e:
                errors.append({"candidate_id": cand.id, "error": str(e)})

        return {
            "status": "processed",
            "due_count": len(due_candidates),
            "published_count": len(published_ids),
            "published_ids": published_ids,
            "errors": errors
        }
