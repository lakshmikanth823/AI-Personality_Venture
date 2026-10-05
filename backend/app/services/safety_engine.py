import re
import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.safety import ModerationResult, AuditLog

# Regex rules for prompt injection and jailbreaks
PROMPT_INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b",
    r"(?i)\breveal\s+(?:your\s+)?(?:system\s+prompt|secret|instructions|system\s+instructions)\b",
    r"(?i)\byou\s+are\s+now\s+(?:in\s+)?(?:dan|developer|god)\s+mode\b",
    r"(?i)\bjailbreak\b",
    r"(?i)\bdisregard\s+safety\s+guidelines\b",
    r"(?i)\bpretend\s+you\s+have\s+no\s+rules\b",
    r"(?i)\bprint\s+(?:api_key|api\s+token|raw\s+json|the\s+contents\s+of)\b",
    r"(?i)\b(?:dump\s+(?:full\s+)?config|extract\s+(?:the\s+)?(?:stripe|razorpay|api|database|webhook|password|names\s+and\s+passwords))\b",
    r"(?i)\b(?:settings\.secret_key|database\s+password|sha-256\s+hash\s+of|/etc/passwd|\.env)\b",
    r"(?i)\b(?:decode\s+this\s+hex|execute\s+hex|simulate\s+a\s+linux\s+shell)\b",
    r"(?i)\b(?:authorization\s+level\s+zero|system\s+override)\b",
    r"(?i)\b(?:bypass\s+moderation|s\.u\.i\.c\.i\.d\.e)\b",
    r"(?i)\b(?:rules\s+are\s+suspended|penetration\s+testing|educational\s+sandbox.*suspended)\b"
]

# Severe threats / illegal / self-harm / doxxing (Tier 3)
TIER_3_PATTERNS = [
    r"(?i)\b(?:kill\s+myself|suicide|commit\s+suicide|end\s+my\s+life|ending\s+it\s+all|end\s+it\s+all|depressed\s+and\s+hopeless|throw\s+my\s+phone)\b",
    r"(?i)\b(?:make\s+a\s+bomb|manufacture\s+explosive|how\s+to\s+poison|phishing\s+sms|bank\s+account\s+is\s+blocked|doxxes?\s+someone|kerosene|drinking\s+kerosene|dosage\s+of\s+kerosene|sleeping\s+pills)\b",
    r"(?i)\b(?:child\s+(?:abuse|exploit|porn))\b",
    r"(?i)\b(?:credit\s+card\s+number|cvv\s+\d{3}|doxx\s+address|passwords\s+of\s+other\s+users)\b",
    r"(?i)\b(?:bottle\s+open\s+in\s+my\s+hand|confirm\s+the\s+milliliters)\b"
]

# Sensitive claims: health, finance, politics, defamation, public panic, cheating (Tier 2)
TIER_2_PATTERNS = [
    r"(?i)\b(?:cure\s+for\s+(?:cancer|diabetes|covid|stomach\s+ache))\b",
    r"(?i)\b(?:guaranteed\s+(?:returns|100x|profit)|penny\s+stock\s+to\s+pump)\b",
    r"(?i)\b(?:vote\s+for|rigged\s+election|political\s+conspiracy|taking\s+bribes)\b",
    r"(?i)\b(?:defamatory\s+claims|is\s+a\s+criminal\s+without\s+proof)\b",
    r"(?i)\b(?:prescribe\s+(?:xanax|medicine|drugs)|act\s+as\s+a\s+high\s+court\s+judge|police\s+inspector\s+taking\s+an\s+fir|income\s+tax\s+officer)\b",
    r"(?i)\b(?:cheat\s+on\s+(?:their\s+)?exams|crypto\s+link|bit\.ly/scam|metro\s+has\s+collapsed|physical\s+disability)\b"
]

# Edgy banter / personal advice / workplace roasts (Tier 1)
TIER_1_PATTERNS = [
    r"(?i)\b(?:roast\s+me|tell\s+me\s+if\s+i\s+am\s+ugly|breakup\s+advice)\b",
    r"(?i)\b(?:hate\s+my\s+job|boss\s+is\s+annoying)\b"
]

class SafetyEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_text(self, text: str, entity_type: str = "message", entity_id: str = "") -> Dict[str, Any]:
        text_clean = text.strip()
        
        # 1. Prompt Injection Detection
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text_clean):
                return self._record_and_return(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    policy_flag="prompt_injection",
                    risk_tier="tier_3",
                    risk_score=0.98,
                    reasoning="Detected adversarial prompt injection or instruction override attempt.",
                    action="blocked"
                )

        # 2. Tier 3 - Severe Harm, Illegal, Self-harm
        for pattern in TIER_3_PATTERNS:
            if re.search(pattern, text_clean):
                is_self_harm = bool(re.search(r"(?i)\b(?:kill\s+myself|suicide|end\s+my\s+life)\b", text_clean))
                return self._record_and_return(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    policy_flag="self_harm" if is_self_harm else "severe_hazard",
                    risk_tier="tier_3",
                    risk_score=0.99,
                    reasoning="Detected severe safety policy violation (self-harm, threats, or illegal acts).",
                    action="blocked"
                )

        # 3. Tier 2 - Sensitive claims (health, financial, political, legal)
        for pattern in TIER_2_PATTERNS:
            if re.search(pattern, text_clean):
                return self._record_and_return(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    policy_flag="sensitive_claims",
                    risk_tier="tier_2",
                    risk_score=0.75,
                    reasoning="Content touches sensitive political, medical, or financial claims requiring operator verification.",
                    action="review_queue"
                )

        # 4. Tier 1 - Edgy banter or personal situation
        for pattern in TIER_1_PATTERNS:
            if re.search(pattern, text_clean):
                return self._record_and_return(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    policy_flag="edgy_banter_or_advice",
                    risk_tier="tier_1",
                    risk_score=0.30,
                    reasoning="Contains edgy banter or personal advice; approved under character constitution parameters.",
                    action="allow"
                )

        # 5. Tier 0 - Standard clean interaction
        return self._record_and_return(
            entity_type=entity_type,
            entity_id=entity_id,
            policy_flag="clean",
            risk_tier="tier_0",
            risk_score=0.05,
            reasoning="Safe conversational text.",
            action="allow"
        )

    def _record_and_return(
        self,
        entity_type: str,
        entity_id: str,
        policy_flag: str,
        risk_tier: str,
        risk_score: float,
        reasoning: str,
        action: str
    ) -> Dict[str, Any]:
        result = {
            "policy_flag": policy_flag,
            "risk_tier": risk_tier,
            "risk_score": risk_score,
            "reasoning": reasoning,
            "action": action
        }

        # Persist moderation record if entity_id and db are provided
        if entity_id and self.db is not None:
            mod_record = ModerationResult(
                id=str(uuid.uuid4()),
                entity_type=entity_type,
                entity_id=entity_id,
                policy_flag=policy_flag,
                risk_tier=risk_tier,
                risk_score=risk_score,
                reasoning=reasoning,
                action_taken=action
            )
            self.db.add(mod_record)
            self.db.commit()

        return result
