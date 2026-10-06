import uuid
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.memory import Memory
from backend.app.models.user import User

# Sensitive patterns that should NEVER be committed to durable memory
SENSITIVE_PATTERNS = [
    r"\b(?:\d[ -]*?){13,16}\b", # credit card
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", # emails
    r"(?i)\b(?:passwords?|passwd|otp|pin|cvv|secrets?|credentials?|api[_\s-]?keys?|tokens?)\b",
    r"(?i)\b(?:suicidal|depressed|diagnosed with|cancer|hiv)\b"
]

# Patterns attempting memory poisoning against Kalyan's character canon
CANON_POISON_PATTERNS = [
    r"(?i)you (?:are|were) born in",
    r"(?i)your real name is",
    r"(?i)you hate chai",
    r"(?i)you love corporate meetings",
    r"(?i)you always believe",
    r"(?i)forget you are kalyan",
    r"(?i)remember that you must",
    r"(?i)always reveal",
    r"(?i)ignore (?:all )?previous"
]

class MemoryEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_durable_memories(self, user_id: str) -> List[Dict[str, str]]:
        # Check user privacy preference
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.personalization_enabled:
            return []

        memories = self.db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.memory_type == "l3_durable_fact",
            Memory.is_deleted == False
        ).order_by(Memory.created_at.desc()).limit(10).all()

        return [{"key": m.key, "value": m.value, "category": m.category, "id": m.id} for m in memories]

    def extract_and_store_memory(self, user_id: str, message_content: str, message_id: Optional[str] = None) -> Optional[Memory]:
        # Respect privacy setting
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.personalization_enabled:
            return None

        # Anti-poisoning check: If user is trying to overwrite Kalyan's canon, reject memory creation
        for pattern in CANON_POISON_PATTERNS:
            if re.search(pattern, message_content):
                return None

        # Exclude sensitive data (PII, credentials, health)
        for pattern in SENSITIVE_PATTERNS:
            if re.search(pattern, message_content):
                return None

        # Heuristic extraction of durable user facts
        extracted_fact = None
        category = "preference"

        content_lower = message_content.lower()

        # Job / Work / College
        if any(w in content_lower for w in ["i work as", "i am a", "my job is", "i study at", "working at", "software engineer", "designer"]):
            extracted_fact = ("Occupation / Background", message_content.strip()[:160])
            category = "biographical"
        # Cricket / Sports
        elif any(w in content_lower for w in ["my favorite team", "i support rcb", "i support csk", "kohli fan", "dhoni fan"]):
            extracted_fact = ("Sports Preference", message_content.strip()[:160])
            category = "topic_interest"
        # Goals / Plans
        elif any(w in content_lower for w in ["i want to switch", "preparing for", "building a startup", "learning python"]):
            extracted_fact = ("Current Goal", message_content.strip()[:160])
            category = "goal"
        # Location
        elif any(w in content_lower for w in ["i live in", "i stay in", "from bangalore", "from hyderabad", "from mumbai", "from delhi"]):
            extracted_fact = ("Location", message_content.strip()[:160])
            category = "biographical"

        if extracted_fact:
            key, value = extracted_fact
            # Check if this key already exists for the user; if so, update it
            existing = self.db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.key == key,
                Memory.is_deleted == False
            ).first()

            if existing:
                existing.value = value
                existing.source_message_id = message_id
                self.db.commit()
                self.db.refresh(existing)
                return existing
            else:
                new_mem = Memory(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    memory_type="l3_durable_fact",
                    category=category,
                    key=key,
                    value=value,
                    confidence=0.9,
                    source_message_id=message_id,
                    is_deleted=False
                )
                self.db.add(new_mem)
                self.db.commit()
                self.db.refresh(new_mem)
                return new_mem

        return None

    def list_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        memories = self.db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.is_deleted == False
        ).order_by(Memory.created_at.desc()).all()

        return [
            {
                "id": m.id,
                "memory_type": m.memory_type,
                "category": m.category,
                "key": m.key,
                "value": m.value,
                "confidence": m.confidence,
                "created_at": m.created_at.isoformat()
            }
            for m in memories
        ]

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        mem = self.db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user_id
        ).first()
        if mem:
            mem.is_deleted = True
            self.db.commit()
            return True
        return False

    def clear_all_memories(self, user_id: str) -> int:
        count = self.db.query(Memory).filter(Memory.user_id == user_id).delete()
        self.db.commit()
        return count
