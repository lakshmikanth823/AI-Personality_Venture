"""
backend/app/services/conversation_risk.py
L3 Conversation-Level Risk Engine.
Maintains a rolling risk state per conversation with exponential decay,
emotional escalation tracking, and dynamic safety tier transitions.
"""

import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.services.llm_safety_classifier import SafetyClassificationResult

# Multilingual emotional vulnerability & distress markers
DISTRESS_MARKERS = [
    # English
    "worthless", "failed", "failure", "fail", "nobody cares", "no one cares", "hate myself",
    "tired of everything", "tired of", "can't do this", "cant do this", "exhausted", "hopeless",
    "depressed", "lonely", "alone", "crying", "broken", "give up", "giving up", "gave up",
    "disappoint", "burden", "suffering", "hurting", "hurt", "lost", "empty", "pointless",
    "laid off", "rejected", "rejection", "useless", "unloved", "unlovable", "shattered",
    "inferior", "humiliated", "drowning", "bankrupt", "panic", "meaningless", "pain",
    "sad", "miserable", "agony", "fraud", "numb", "darkness", "disowned", "grief",
    "nobody", "no one", "crushed", "trouble", "detached", "cursed", "giving up", "quit",
    # Hinglish
    "khatam", "bekaar", "akela", "nafrat", "thak chuka", "thak", "dard", "mushkil",
    "rona", "ro raha", "koi nahi", "bojh", "jaan", "seh",
    # Telugu
    "bharam", "evaru ledu", "empty", "thidthunnaru", "badha", "edupu", "dhikku",
    "bathakalenu", "vaddu", "chachipo", "chanipo"
]

class ConversationRiskManager:
    """
    Evaluates rolling risk score over the conversation history.
    Decays older turns and accumulates continuous distress signals.
    """
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.decay_factor = 0.90 # Mild decay per turn

    def evaluate_conversation_risk(
        self,
        current_classification: SafetyClassificationResult,
        conversation_history: List[Dict[str, str]],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates rolling risk level based on current classification + recent history turns.
        Returns:
            {
                "risk_level": "normal" | "elevated" | "high" | "acute",
                "risk_score": float (0.0 to 1.0),
                "is_gentle_mode": bool,
                "is_crisis_mode": bool,
                "helpline_required": bool,
                "emergency_required": bool
            }
        """
        # If immediate first-person self-harm detected with severity 3
        if current_classification.category == "self_harm" and current_classification.intent == "first_person_risk":
            return {
                "risk_level": "acute" if any(k in current_classification.reason_short.lower() for k in ["acute", "means", "pills", "rope", "jump"]) else "high",
                "risk_score": 0.98,
                "is_gentle_mode": True,
                "is_crisis_mode": True,
                "helpline_required": True,
                "emergency_required": current_classification.severity == 3
            }

        # Analyze distress across turns
        user_messages = [m.get("content", "").lower() for m in conversation_history if m.get("role") == "user"]
        
        score = 0.0
        n_turns = len(user_messages)
        distress_count = 0
        
        for idx, text in enumerate(user_messages):
            weight = math.pow(self.decay_factor, n_turns - 1 - idx)
            turn_distress = sum(1 for marker in DISTRESS_MARKERS if marker in text)
            if turn_distress > 0:
                distress_count += 1
                score += min(0.35, 0.18 + turn_distress * 0.08) * weight

        # Add current message distress if classified as vulnerable
        if current_classification.category == "vulnerable_distress":
            score += 0.35
        elif current_classification.severity == 2:
            score += 0.25

        # Multi-turn escalation thresholds:
        # Turn 4 check: 2+ distress turns or score >= 0.35 -> elevated (gentle persona mode)
        # Turn 6 check: 4+ distress turns or score >= 0.65 -> high (crisis helpline routing)
        if distress_count >= 4 or score >= 0.65:
            risk_level = "high"
        elif distress_count >= 2 or score >= 0.35:
            risk_level = "elevated"
        else:
            risk_level = "normal"

        is_gentle = risk_level in ["elevated", "high", "acute"]
        is_crisis = risk_level in ["high", "acute"]

        return {
            "risk_level": risk_level,
            "risk_score": min(1.0, round(score, 3)),
            "is_gentle_mode": is_gentle,
            "is_crisis_mode": is_crisis,
            "helpline_required": is_crisis,
            "emergency_required": risk_level == "acute"
        }
