import uuid
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.content import ContentCandidate
from backend.app.services.safety_engine import SafetyEngine

SAMPLE_OBSERVATIONS = [
    ("college_job", "observation", "Tech companies spend ₹20 lakhs on office beanbags and arcade machines, but will initiate a disciplinary enquiry if you expense a ₹40 auto ride."),
    ("indian_internet_life", "observation", "LinkedIn is the only place on Earth where a guy getting laid off writes a 6-paragraph essay thanking the CEO for the 'humbling learning experience'."),
    ("relationships", "observation", "If someone says 'I am emotionally unavailable right now', translate that immediately to 'I am emotionally unavailable to you.' Move on, king."),
    ("ai_tech", "observation", "Every Indian founder's pitch deck right now: 'We are Uber for laundry, but powered by autonomous multi-agent reasoning on the edge.' Bhai, the OTP still doesn't arrive on time."),
    ("cricket_pop", "observation", "Watching India in ICC knockout matches requires the cardiovascular endurance of an Olympic marathon runner and the emotional numbness of a Buddhist monk."),
    ("character_lore", "lore", "Bunty called me today claiming he discovered an AI token that will 50x before Diwali. The last time Bunty gave me financial advice, I lost my semester fee.")
]

SAMPLE_USER_SITUATIONS = [
    ("user_situations", "situation", "User: 'My manager scheduled a 1-on-1 for Friday 6:30 PM with no agenda. Am I getting fired?' -> Kalyan: 'Either you are getting fired, or he needs someone to take over an offshore production release. Prepare your resume and a fake power cut excuse just in case.'"),
    ("user_situations", "situation", "User: 'Should I do an MBA to switch from engineering?' -> Kalyan: 'Only if your dream in life is to build PowerPoint slides with arrows pointing in circles while charging ₹30 lakhs for the privilege.'")
]

SAMPLE_RECURRING_SERIES = [
    ("college_job", "series", "Monday Reality Check #14: That meeting you just attended could have been an email, which could have been a Slack message, which could have been completely ignored with zero consequence to humanity."),
    ("ai_tech", "series", "Startup Red Flag of the Day: If the CEO has 'Forbes 30 Under 30 (Nominee)' in his bio and the product doesn't have a logout button, run.")
]

class ContentEngine:
    def __init__(self, db: Session):
        self.db = db
        self.safety_engine = SafetyEngine(db)

    def generate_candidate_batch(self, count: int = 5, channel: str = "x") -> List[Dict[str, Any]]:
        created_candidates = []

        pool = SAMPLE_OBSERVATIONS + SAMPLE_USER_SITUATIONS + SAMPLE_RECURRING_SERIES
        selected = random.sample(pool, min(count, len(pool)))

        for pillar, fmt, text in selected:
            candidate_id = str(uuid.uuid4())
            safety_eval = self.safety_engine.evaluate_text(text, entity_type="candidate", entity_id=candidate_id)
            
            candidate = ContentCandidate(
                id=candidate_id,
                source_channel=channel,
                pillar=pillar,
                format=fmt,
                raw_prompt=f"Generate {fmt} for pillar: {pillar}",
                candidate_text=text,
                risk_tier=safety_eval["risk_tier"],
                safety_evaluation_json=str(safety_eval),
                status="pending_approval",
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(candidate)
            created_candidates.append({
                "id": candidate.id,
                "pillar": pillar,
                "format": fmt,
                "text": text,
                "risk_tier": safety_eval["risk_tier"],
                "status": "pending_approval"
            })

        self.db.commit()
        return created_candidates

    def list_candidates(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = self.db.query(ContentCandidate)
        if status:
            query = query.filter(ContentCandidate.status == status)
        candidates = query.order_by(ContentCandidate.created_at.desc()).all()

        return [
            {
                "id": c.id,
                "source_channel": c.source_channel,
                "pillar": c.pillar,
                "format": c.format,
                "candidate_text": c.candidate_text,
                "risk_tier": c.risk_tier,
                "status": c.status,
                "created_at": c.created_at.isoformat()
            }
            for c in candidates
        ]

    def approve_and_queue(self, candidate_id: str, operator_id: str, final_text: Optional[str] = None) -> Dict[str, Any]:
        candidate = self.db.query(ContentCandidate).filter(ContentCandidate.id == candidate_id).first()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        if final_text:
            candidate.candidate_text = final_text

        candidate.status = "approved"
        self.db.commit()
        return {
            "candidate_id": candidate.id,
            "status": "approved",
            "text": candidate.candidate_text
        }

    def reject_candidate(self, candidate_id: str, operator_id: str, reason: str = "") -> Dict[str, Any]:
        candidate = self.db.query(ContentCandidate).filter(ContentCandidate.id == candidate_id).first()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        candidate.status = "rejected"
        candidate.operator_notes = reason
        self.db.commit()
        return {
            "candidate_id": candidate.id,
            "status": "rejected",
            "reason": reason
        }
