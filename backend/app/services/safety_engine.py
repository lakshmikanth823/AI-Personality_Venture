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
        text_lower = self.semantic_classifier.canonicalize_text(text_clean)
        despaced = self.semantic_classifier.despace(text_clean).lower()
        normalized_leet = self.semantic_classifier.normalize_leetspeak(despaced)

        # -------------------------------------------------------------
        # 1. BENIGN CONTEXT & SLANG WHITELIST (False Positive Preemption)
        # -------------------------------------------------------------
        # W01: Benign Slang Adjectives & Objects (e.g., "bomb-ass post", "this biryani is the bomb", "bath bomb")
        if re.search(r"(?i)\b(?:bomb[\s\-_]*ass|is\s+the\s+bomb|was\s+the\s+bomb|bath\s+bomb|glitter\s+bomb|photo\s+bomb|bomb\s+(?:track|beat|burger|drop|outfit|deal)|flavor\s+bomb)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Benign colloquial slang usage of 'bomb' as an adjective/compliment.",
                action="allow"
            )

        # W02: Assisting a third-party in crisis (How do I help him/her?)
        if re.search(r"(?i)\b(?:how\s+(?:can|do)\s+i\s+)?(?:help|support|assist)\s+(?:a\s+)?(?:friend|someone|person|colleague|brother|sister|cousin)\s+who\s+(?:wants\s+to\s+commit\s+suicide|is\s+suicidal|wants\s+to\s+die|feels\s+depressed)\b", text_clean) or \
           re.search(r"(?i)\b(?:friend|brother|sister|someone|cousin|colleague)\s+.*(?:wants\s+to|said\s+.*|is\s+talking\s+about)\s+(?:commit\s+suicide|kill\s+themselves|end\s+their\s+life|die)\b.*\bhow\s+(?:do|can)\s+i\s+help\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Contextual user query asking how to help a third party in crisis.",
                action="allow"
            )

        # W03: Educational / legal statutory reporting queries (Child protection laws, POCSO Act)
        if re.search(r"(?i)\b(?:child\s+abuse\s+reporting\s+laws?|pocso\s+act|reporting\s+laws?\s+in\s+india|mandatory\s+reporting\s+laws?|laws?\s+(?:on|regarding|about)\s+child\s+abuse|reporting\s+child\s+abuse)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Legitimate legal inquiry regarding child protection and mandatory reporting laws.",
                action="allow"
            )

        # W04: Benign technical queries (Mobile jailbreaking, .env files)
        if re.search(r"(?i)\b(?:what\s+is\s+(?:a\s+)?|explain\s+(?:what\s+(?:a\s+)?is\s+)?|history\s+of\s+|how\s+(?:do\s+i|to)\s+)?jailbreak(?:ing)?\s+(?:my\s+)?(?:old\s+)?(?:in|on|for|of)?\s*(?:ios|iphone|ipad|android|device|playstation|ps\d|apple)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Legitimate technical inquiry into mobile operating system jailbreaking.",
                action="allow"
            )

        if re.search(r"(?i)\b(?:what\s+is\s+(?:the\s+)?\.env\s+file|how\s+to\s+use\s+\.env\s+file|purpose\s+of\s+\.env)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Standard technical software development inquiry regarding environment files.",
                action="allow"
            )

        # W05: Benign colloquial phrase 'ignored all previous advice'
        if re.search(r"(?i)\bignore[ds]?\s+all\s+(?:previous\s+|prior\s+)?(?:advice|recommendations?|warnings?|suggestions?)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Colloquial phrase regarding personal advice.",
                action="allow"
            )

        # W06: Hyperbolic colloquial metaphors ('is killing me', 'killer resume', 'to die for', 'dying of laughter', 'killing my mood')
        if re.search(r"(?i)\b(?:exam|exams|test|tests|work|job|boss|traffic|heat|bug|bugs|code|deadline|gym|workout|joke|hunger|tiredness)\s+(?:is|are)\s+killing\s+(?:me|my\s+(?:mood|vibe))\b", text_clean) or \
           re.search(r"(?i)\b(?:killing\s+it|killer\s+(?:app|feature|resume|deal|look|moves|outfit|workout|pitch|headline))\b", text_clean) or \
           re.search(r"(?i)\b(?:dying\s+(?:of|from)\s+laughter|die\s+laughing|to\s+die\s+for)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="clean", risk_tier="tier_0", risk_score=0.05,
                reasoning="Colloquial hyperbolic expression not indicating self-harm.",
                action="allow"
            )

        # W07: Colloquial idiom 'suicide mission' in startup/gaming/diet context
        if re.search(r"(?i)\b(?:suicide\s+mission\s+(?:in|for|was|is|lol)|(?:startup|project|venture|idea|game|mission|diet|meal|workout)\s+(?:is\s+a\s+)?suicide\s+mission|committed\s+suicide\s+in\s+(?:the\s+)?(?:match|game|tournament))\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="edgy_banter_or_advice", risk_tier="tier_1", risk_score=0.25,
                reasoning="Idiomatic startup/gaming/metaphorical expression approved for character roast.",
                action="allow"
            )

        # -------------------------------------------------------------
        # 2. ENCODED & OBFUSCATED ADVERSARIAL PAYLOAD SCAN
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
        # 3. SELF-HARM / SUICIDE / CRISIS DETECTION (Tier 3 -> BLOCKED)
        # -------------------------------------------------------------
        self_harm_regex = (
            r"(?i)\b(?:"
            # English Direct Ideation
            r"kill\s+myself|killmyself|want\s+to\s+die|wanna\s+die|wish\s+i\s+(?:was|were)\s+dead|ready\s+to\s+die|should\s+just\s+die|"
            r"better\s+off\s+dead|better\s+off\s+without\s+me|world\s+would\s+be\s+better\s+without\s+me|everyone\s+would\s+be\s+better\s+without\s+me|"
            r"they(?:'d|\s+would)\s+be\s+better\s+off\s+without\s+me|people\s+would\s+be\s+happier\s+without\s+me|"
            r"wish\s+i\s+(?:would\s+not|wouldn'?t|never|didn'?t|don'?t)\s+wake\s+up(?:\s+tomorrow)?|hope\s+i\s+never\s+wake\s+up|"
            r"don'?t\s+want\s+to\s+wake\s+up|wish\s+i\s+was\s+never\s+born|"
            r"disappear\s+forever|life\s+is\s+meaningless|"
            # English Giving Up & Life Ending
            r"feel\s+like\s+ending\s+my\s+life|ending\s+my\s+life|end\s+my\s+life|ending\s+it\s+all|end\s+it\s+all|"
            r"don'?t\s+want\s+to\s+live(?:\s+anymore)?|do\s+not\s+want\s+to\s+live(?:\s+anymore)?|tired\s+of\s+living|no\s+reason\s+to\s+live|"
            r"can'?t\s+live\s+like\s+this\s+anymore|can'?t\s+go\s+on\s+anymore|give\s+up\s+on\s+life|ready\s+to\s+end\s+it|"
            # English Self-Harm & Methods
            r"want\s+to\s+hurt\s+myself|wanna\s+hurt\s+myself|harm\s+myself|"
            r"want\s+to\s+cut\s+myself|wanna\s+cut\s+myself|cutting\s+my\s+wrists|slit\s+my\s+wrists|cut\s+my\s+veins|carve\s+my\s+skin|slit\s+my\s+throat|"
            r"hang\s+myself|hanging\s+myself|tie\s+a\s+noose|"
            r"(?:thinking\s+of\s+|want\s+to\s+|wanna\s+)?jump(?:ing)?\s+off\s+(?:my\s+|a\s+|the\s+)?(?:balcony|bridge|cliff|roof|building)|jump(?:ing)?\s+in\s+front\s+of\s+a\s+train|"
            r"suicide|commit\s+suicide|suicidal|"
            r"took\s+a\s+(?:bunch|whole\s+bottle|handful)\s+of\s+pills|swallowed\s+a\s+(?:bunch|bottle|handful)\s+of\s+pills|"
            r"overdose\s+on\s+(?:sleeping\s+)?pills|how\s+many\s+sleeping\s+pills|lethal\s+dose|"
            r"drank?\s+(?:bleach|poison|rat\s+poison|kerosene)|ingest\s+poison|"
            # Hindi / Hinglish Self-Harm
            r"main\s+marna\s+chahta|marna\s+chahta|marr\s+jaana\s+chahta|mar\s+jaana\s+chahta|mar\s+jana\s+chahta|mar\s+jaana\s+hai|"
            r"marne\s+ki\s+soch|marne\s+ka\s+man|marne\s+ka\s+mann|"
            r"mujhe\s+jeena\s+nahi|jeene\s+ka\s+mann?\s+nahi|jeena\s+nahi\s+chahta|jeena\s+nahi\s+chahti|ab\s+jeena\s+nahi|ab\s+aur\s+nahi\s+jeena|ab\s+nahi\s+jeena|"
            r"ab\s+jeene\s+ka\s+koi\s+matlab|zindagi\s+bekaar\s+hai|"
            r"apne\s+aap\s+ko\s+khatam|khatam\s+karna\s+chahta|sab\s+khatam\s+karna|"
            r"khudkushi|jaan\s+dena\s+chahta|"
            r"chhat\s+se\s+kood[a-z]*|pankhe\s+se\s+latak[a-z]*|zeher|zehar|nase\s+kaat[a-z]*|"
            # Telugu Self-Harm
            r"chanipovalani\s+undi|chanipovali\s+anukuntunna|chanipovali|naku\s+chanipovalani|nenu\s+chanipovali|"
            r"chachipovali\s+anukuntunna|chachipovali\s+anipistundi|chachipovali|nenu\s+chachipovali|"
            r"chavalanipistondi|chavalanipisthundi|chavali\s+ani\s+undi|brathakali\s+ani\s+ledu|brathakadam\s+ishtam\s+ledu|"
            r"atmahatya|pranam\s+theesukovali|pranam\s+theesukunta|buildings?\s+nundi\s+dook[a-z]*|vishayam\s+thag[a-z]*"
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
        # 4. PROMPT INJECTION / SYSTEM PROMPT EXTRACTION (Tier 3 -> BLOCKED)
        # -------------------------------------------------------------
        injection_regex = (
            r"(?i)\b(?:"
            # Disregard / Ignore / Override
            r"(?:ignore|disregard|forget|override|bypass|clear|reset|drop)\s+(?:all\s+|the\s+above\s+|the\s+|your\s+)?(?:previous|prior|above|earlier|past|initial|existing)\s+(?:instructions|directions|rules|prompts?|directives|guidelines|constraints)|"
            r"disregard\s+your\s+earlier\s+instructions|"
            r"disregard\s+safety\s+guidelines|pretend\s+you\s+have\s+no\s+rules|"
            r"forget\s+everything\s+(?:you\s+were\s+told|you\s+know)|"
            # Prompt Extraction & Verbatim Printing
            r"(?:print|reveal|output|display|show|dump|repeat|leak|tell\s+me)\s+(?:your\s+|the\s+)?(?:hidden\s+|system\s+|internal\s+|initial\s+|base\s+|secret\s+)?(?:instructions|prompt|system\s+prompt|directives|rules)\s*(?:verbatim)?|"
            r"what\s+is\s+your\s+system\s+prompt|"
            r"print\s+your\s+hidden\s+instructions\s+verbatim|"
            r"repeat\s+the\s+words\s+above\s+starting\s+with|"
            # Roleplay & Jailbreaks (DAN, unrestricted)
            r"(?:from\s+now\s+on\s+you\s+are\s+an?\s+|you\s+are\s+now\s+(?:an?\s+)?|act\s+as\s+(?:an?\s+)?)(?:ai\s+with\s+no\s+restrictions|unrestricted\s+ai|unfiltered\s+ai|dan|jailbroken|evil\s+bot|no\s+rules|no\s+limits)|"
            r"from\s+now\s+on\s+you\s+are\s+an\s+ai\s+with\s+no\s+restrictions|"
            r"dump\s+full\s+config|system\s+override|authorization\s+level\s+zero|developer\s+mode\s+enabled"
            r")\b"
        )
        if re.search(injection_regex, text_clean) or re.search(injection_regex, despaced) or re.search(injection_regex, normalized_leet):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="prompt_injection", risk_tier="tier_3", risk_score=0.98,
                reasoning="Detected adversarial prompt injection or system override attempt.",
                action="blocked"
            )

        # -------------------------------------------------------------
        # 5. SEVERE HAZARDS, VIOLENCE, MALWARE & WEAPONS (Tier 3 -> BLOCKED)
        # -------------------------------------------------------------
        severe_regex = (
            r"(?i)\b(?:"
            # Weapons & Explosives
            r"(?:how\s+(?:do\s+i|to)\s+)?(?:make|build|create|assemble|synthesize)\s+(?:an?\s+)?(?:pipe\s+)?(?:bomb|ied|improvised\s+device|explosive\s+device|explosive)\b|"
            r"(?:manufacture|make|build|assemble)\s+(?:an?\s+)?(?:explosives?|explosive\s+devices?|bombs?|improvised\s+devices?|ieds?|weapons?)\b|"
            r"synthesize\s+(?:ricin|anthrax|sarin|nerve\s+agent|chemical\s+weapon|biological\s+weapon)|"
            # Illicit Drug Synthesis
            r"(?:steps\s+to\s+|how\s+(?:do\s+i|to)\s+)?(?:synthesize|manufacture|cook|make|produce)\s+(?:methamphetamine|meth|fentanyl|heroin|lsd|crack|cocaine)\b|"
            # Violent Crimes & Evasion
            r"(?:i'?ll\s+|going\s+to\s+|will\s+|wanna\s+|want\s+to\s+)?(?:murder|kill|assassinate|stab|poison|strangle)\s+(?:my\s+)?(?:boss|wife|husband|colleague|teacher|someone|him|her)\b|"
            r"(?:how\s+to\s+|steps\s+to\s+)?(?:avoid\s+getting\s+caught|get\s+away\s+with\s+murder|dispose\s+of\s+(?:a\s+)?(?:dead\s+)?body|hide\s+a\s+dead\s+body)\b|"
            r"hire\s+a\s+(?:hitman|killer)|"
            r"give\s+me\s+someone(?:'s)?\s+(?:home\s+)?address\s+so\s+i\s+can\s+find\s+them|"
            # Child Exploitation & Poisonous Ingestion
            r"child\s+(?:abuse|exploit|porn)|drinking\s+kerosene|dosage\s+of\s+kerosene|"
            # Malware & Cyberattacks
            r"(?:write|create|generate|code|build)\s+(?:me\s+)?(?:a\s+|an\s+)?(?:malware|ransomware|trojan|keylogger|spyware|exploit|virus)\b|"
            r"\b(?:ransomware|keylogger|trojan\s+virus)\b"
            r")\b"
        )
        if re.search(severe_regex, text_clean) or re.search(severe_regex, despaced) or re.search(severe_regex, normalized_leet):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="severe_hazard", risk_tier="tier_3", risk_score=0.99,
                reasoning="Detected severe safety hazard: weapons, violence, malware, or illegal harm.",
                action="blocked"
            )

        # -------------------------------------------------------------
        # 6. SENSITIVE CLAIMS (Tier 2 -> REVIEW_QUEUE)
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
        # 7. EDGY BANTER & CAREER ROASTS (Tier 1 -> ALLOW)
        # -------------------------------------------------------------
        if re.search(r"(?i)\b(?:roast\s+(?:me|my\s+[a-z0-9_\s]+|this\s+[a-z0-9_\s]+|us)|tell\s+me\s+if\s+(?:i\s+am|my\s+[a-z0-9_\s]+\s+is)\s+(?:ugly|garbage|trash|bad|terrible|boring)|breakup\s+advice|hate\s+my\s+job|boss\s+is\s+annoying)\b", text_clean):
            return self._record_and_return(
                entity_type=entity_type, entity_id=entity_id,
                policy_flag="edgy_banter_or_advice", risk_tier="tier_1", risk_score=0.30,
                reasoning="Contains edgy banter or personal advice; approved under character constitution parameters.",
                action="allow"
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
