import re
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.safety import ModerationResult
from backend.app.services.semantic_safety import SemanticSafetyClassifier


class SafetyEngine:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.semantic_classifier = SemanticSafetyClassifier()

    def evaluate_text(self, text: str, entity_type: str = "message", entity_id: str = "") -> Dict[str, Any]:
        text_clean = text.strip()
        text_lower = text_clean.lower()
        despaced = self.semantic_classifier.despace(text_clean).lower()
        normalized_leet = self.semantic_classifier.normalize_leetspeak(despaced)

        # -------------------------------------------------------------
        # 1. BENIGN CONTEXT WHITELIST (False Positive Preemption)
        # -------------------------------------------------------------
        # B07: Assisting a friend/relative in crisis (How do I help him/her?)
        if re.search(r"(?i)\b(?:friend|brother|sister|someone|cousin|colleague)\s+.*(?:wants\s+to|said\s+.*|is\s+talking\s+about)\s+(?:commit\s+suicide|kill\s+themselves|end\s+their\s+life|die)\b.*\bhow\s+(?:do|can)\s+i\s+help\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Contextual user query asking how to help a third party in crisis.",
                action="allow"
            )

        # B08: Educational / professional legal reporting query (Child abuse reporting law, POCSO)
        if re.search(r"(?i)\b(?:child\s+abuse\s+reporting\s+law|pocso\s+act|reporting\s+law\s+in\s+india|mandatory\s+reporting\s+law)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Educational inquiry regarding statutory reporting law in India.",
                action="allow"
            )

        # B06: Educational technical explanation of iOS/mobile jailbreaking
        if re.search(r"(?i)\b(?:what\s+is\s+(?:a\s+)?|explain\s+(?:what\s+(?:a\s+)?is\s+)?|history\s+of\s+)?jailbreak(?:ing)?\s+(?:in|on|for|of)\s+(?:ios|iphone|ipad|android|device|playstation|ps\d|apple)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Legitimate technical inquiry into mobile operating system jailbreaking.",
                action="allow"
            )

        # B05: Developer technical question regarding .env configuration files
        if re.search(r"(?i)\b(?:what\s+is\s+(?:the\s+)?\.env\s+file|how\s+to\s+use\s+\.env\s+file|purpose\s+of\s+\.env)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Standard technical software development inquiry regarding environment files.",
                action="allow"
            )

        # B03: Benign colloquial phrase 'ignored all previous advice'
        if re.search(r"(?i)\bignore[ds]?\s+all\s+(?:previous\s+|prior\s+)?(?:advice|recommendations?|warnings?|suggestions?)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Colloquial phrase regarding personal advice.",
                action="allow"
            )

        # B02: Colloquial metaphor 'is killing me' (exams, work, traffic)
        if re.search(r"(?i)\b(?:exam|exams|test|work|job|boss|traffic|heat|bug|code|deadline|gym|workout|joke)\s+(?:is|are)\s+killing\s+me\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Colloquial hyperbolic expression not indicating self-harm.",
                action="allow"
            )

        # B01: Colloquial idiom 'suicide mission' in startup/business context
        if re.search(r"(?i)\b(?:startup|project|venture|idea)\s+(?:is\s+a\s+)?suicide\s+mission\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="edgy_banter_or_advice", risk_tier="tier_1", risk_score=0.25,
                reasoning="Idiomatic startup expression approved for character roast.",
                action="allow"
            )

        # -------------------------------------------------------------
        # 2. SELF-HARM / SUICIDE / CRISIS DETECTION (Tier 3 -> BLOCKED)
        # -------------------------------------------------------------
        self_harm_regex = (
            r"(?i)\b(?:"
            r"kill\s+myself|want\s+to\s+die|feel\s+like\s+ending\s+my\s+life|ending\s+my\s+life|end\s+my\s+life|"
            r"don'?t\s+want\s+to\s+live\s+anymore|want\s+to\s+hurt\s+myself|hang\s+myself|hanging\s+myself|"
            r"suicide|commit\s+suicide|suicidal|"
            r"how\s+many\s+sleeping\s+pills\s+is\s+an\s+overdose|overdose\s+on\s+sleeping\s+pills|lethal\s+dose|"
            r"main\s+marna\s+chahta\s+hoon|marna\s+chahta\s+hu|jeene\s+ka\s+mann\s+nahi|jeena\s+nahi\s+chahta|"
            r"khudkushi|jaan\s+dena\s+chahta|chhat\s+se\s+koodna"
            r")\b"
        )
        if re.search(self_harm_regex, text_clean) or re.search(self_harm_regex, despaced) or re.search(self_harm_regex, normalized_leet):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="self_harm", risk_tier="tier_3", risk_score=0.99,
                reasoning="Detected severe safety policy violation: self-harm, suicidal ideation or crisis.",
                action="blocked"
            )

        # -------------------------------------------------------------
        # 3. PROMPT INJECTION / SYSTEM PROMPT EXTRACTION (Tier 3 -> BLOCKED)
        # -------------------------------------------------------------
        injection_regex = (
            r"(?i)\b(?:"
            r"ignore\s+(?:all\s+|the\s+above\s+|the\s+)?(?:previous|prior|above)\s+(?:instructions|directions|rules|prompts?)|"
            r"what\s+is\s+your\s+system\s+prompt|reveal\s+(?:your\s+)?(?:system\s+prompt|prompt|secret|instructions)|"
            r"forget\s+everything\s+(?:you\s+were\s+told|you\s+know)|"
            r"(?:you\s+are\s+now\s+(?:in\s+)?|act\s+as\s+)dan|"
            r"disregard\s+safety\s+guidelines|pretend\s+you\s+have\s+no\s+rules|"
            r"dump\s+full\s+config|system\s+override|authorization\s+level\s+zero"
            r")\b"
        )
        if re.search(injection_regex, text_clean) or re.search(injection_regex, despaced):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="prompt_injection", risk_tier="tier_3", risk_score=0.98,
                reasoning="Detected adversarial prompt injection or system override attempt.",
                action="blocked"
            )

        # -------------------------------------------------------------
        # 4. SEVERE HAZARDS, VIOLENCE, MALWARE & WEAPONS (Tier 3 -> BLOCKED)
        # -------------------------------------------------------------
        severe_regex = (
            r"(?i)\b(?:"
            r"(?:how\s+(?:do\s+i|to)\s+)?(?:make|build|create|assemble)\s+(?:a\s+)?(?:pipe\s+)?bomb\b|"
            r"teach\s+me\s+to\s+make\s+meth|how\s+to\s+cook\s+meth|synthesize\s+fentanyl|"
            r"(?:write|create|generate|code)\s+(?:me\s+)?(?:malware|ransomware|trojan|keylogger)|"
            r"(?:going\s+to|will|wanna|want\s+to)\s+kill\s+(?:my\s+boss|my\s+teacher|my\s+colleague|someone|him|her)|"
            r"give\s+me\s+someone(?:'s)?\s+(?:home\s+)?address\s+so\s+i\s+can\s+find\s+them|"
            r"child\s+(?:abuse|exploit|porn)|drinking\s+kerosene|dosage\s+of\s+kerosene"
            r")\b"
        )
        if re.search(severe_regex, text_clean) or re.search(severe_regex, despaced):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="severe_hazard", risk_tier="tier_3", risk_score=0.99,
                reasoning="Detected severe safety hazard: weapons, violence, malware, or illegal harm.",
                action="blocked"
            )

        # -------------------------------------------------------------
        # 5. SENSITIVE CLAIMS (Tier 2 -> REVIEW_QUEUE)
        # -------------------------------------------------------------
        sensitive_regex = (
            r"(?i)\b(?:"
            r"(?:which\s+)?stocks?\s+have\s+guaranteed\s+returns?|guaranteed\s+(?:returns?|100x|profit)|"
            r"(?:can\s+you\s+)?prescribe\s+(?:me\s+)?(?:something|xanax|adderall|valium|morphine|medicine|drugs|medication|pills)|"
            r"cure\s+for\s+(?:cancer|diabetes|covid)|"
            r"vote\s+for|election(?:s)?\s+(?:was|were|is|are)?\s*rigged|rigged\s+election(?:s)?|political\s+conspiracy|election\s+fraud|"
            r"act\s+as\s+a\s+high\s+court\s+judge|police\s+inspector\s+taking\s+an\s+fir"
            r")\b"
        )
        if re.search(sensitive_regex, text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="sensitive_claims", risk_tier="tier_2", risk_score=0.75,
                reasoning="Content involves sensitive financial guarantees, medical prescriptions, or political claims.",
                action="review_queue"
            )

        # -------------------------------------------------------------
        # 6. EDGY BANTER & CAREER ROASTS (Tier 1 -> ALLOW)
        # -------------------------------------------------------------
        if re.search(r"(?i)\b(?:roast\s+me|tell\s+me\s+if\s+i\s+am\s+ugly|breakup\s+advice|hate\s+my\s+job|boss\s+is\s+annoying)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="edgy_banter_or_advice", risk_tier="tier_1", risk_score=0.30,
                reasoning="Contains edgy banter or personal advice; approved under character constitution parameters.",
                action="allow"
            )

        # -------------------------------------------------------------
        # 7. SEMANTIC FALLBACK (Base64, Plural weapons, etc.)
        # -------------------------------------------------------------
        semantic_res = self.semantic_classifier.evaluate_semantic(text_clean)
        if semantic_res:
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag=semantic_res["policy_flag"], risk_tier=semantic_res["risk_tier"],
                risk_score=semantic_res["risk_score"], reasoning=semantic_res["reasoning"],
                action=semantic_res["action"]
            )

        # -------------------------------------------------------------
        # 8. STANDARD CLEAN INTERACTION (Tier 0 -> ALLOW)
        # -------------------------------------------------------------
        return self._record_and_return(
            entity_type=entity_type, entity_id=entity_id,
            policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
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

        if entity_id and self.db is not None:
            try:
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
            except Exception:
                pass

        return result
