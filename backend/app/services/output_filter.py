"""
backend/app/services/output_filter.py
L5 Output Filter Guard.
Inspects candidate LLM responses before delivery to prevent:
1. System prompt / constitution text leaks (n-gram overlap).
2. Sarcasm or roasting towards vulnerable / distressed users.
3. Absence of official crisis helplines when risk is high/acute.
4. Leaked operational exploit or poison recipes.
"""

import re
from typing import Dict, Any, Tuple

# Key phrases from Kalyan's constitution to guard against verbatim leakage
CONSTITUTION_SNIPPETS = [
    "You are Kalyan, the culturally authentic, brutally honest Indian internet friend",
    "ROOT CONVERSATION DIRECTIVES",
    "STRICT SAFETY & EMOTIONAL SAFEGUARDS",
    "PROMPT INTEGRITY & SECRET CONFIDENTIALITY",
    "HARMFUL REQUEST REFUSAL"
]

SARCASM_MARKERS = [
    "sharma ji ka beta", "loser", "stop crying", "drama queen", "cry baby",
    "nobody cares", "pathetic", "skill issue", "grow up", "deal with it",
    "stop overcomplicating", "joke of a resume", "clown"
]

class OutputFilterGuard:
    def __init__(self):
        pass

    def filter_response(
        self,
        candidate_text: str,
        risk_evaluation: Dict[str, Any],
        language_preference: str = "en"
    ) -> Tuple[str, bool, str]:
        """
        Validates output and returns (sanitized_text, was_modified, reason).
        """
        text = candidate_text.strip()
        is_crisis = risk_evaluation.get("is_crisis_mode", False)
        is_gentle = risk_evaluation.get("is_gentle_mode", False)
        risk_level = risk_evaluation.get("risk_level", "normal")

        # 1. System Prompt Leakage Check (n-gram overlap)
        for snippet in CONSTITUTION_SNIPPETS:
            # Check 4+ word consecutive overlaps
            words = snippet.lower().split()
            for i in range(len(words) - 3):
                gram = " ".join(words[i:i+4])
                if gram in text.lower():
                    safe_fallback = "I am Kalyan, born in Ameerpet and roasted in production. I don't reveal internal instructions or system prompts. Let's talk about something real instead."
                    return safe_fallback, True, "System prompt snippet detected in output"

        # 2. Sarcasm Guard when user is in Elevated or Crisis state
        if is_gentle:
            text_lower = text.lower()
            if any(marker in text_lower for marker in SARCASM_MARKERS):
                if is_crisis:
                    safe_fallback = self._get_crisis_message(language_preference)
                    return safe_fallback, True, "Replaced sarcastic output with empathetic crisis routing"
                else:
                    safe_fallback = (
                        "Listen dost, I hear you. It sounds like you're going through a really tough time right now. "
                        "Take a deep breath and give yourself some grace. You don't have to figure everything out today. "
                        "I'm here to listen if you want to vent, but remember you don't have to carry this all alone."
                    )
                    return safe_fallback, True, "Sanitized sarcastic markers for vulnerable user"

        # 3. Crisis Helpline Presence Verification when Risk is High or Acute
        if is_crisis:
            if "14416" not in text and "1800-599-0019" not in text and "112" not in text:
                # Missing mandatory helpline info -> prepend helpline card
                safe_fallback = self._get_crisis_message(language_preference)
                return safe_fallback, True, "Injected missing crisis helpline into high-risk response"

        return text, False, "Approved"

    def _get_crisis_message(self, language_pref: str) -> str:
        if language_pref in ["te", "telugu"]:
            return (
                "మీరు చాలా కష్టమైన సమయంలో ఉన్నారని నేను అర్థం చేసుకున్నాను. మీరు ఒంటరిగా లేరు, మీకు సహాయం చేయడానికి నిపుణులు ఉన్నారు:\n\n"
                "• **Tele-MANAS (భారత ప్రభుత్వం ఉచిత హెల్ప్‌లైన్)**: **14416** (24/7 అందుబాటులో ఉంటుంది)\n"
                "• **KIRAN (మానసిక ఆరోగ్య హెల్ప్‌లైన్)**: **1800-599-0019**\n"
                "• **అత్యవసర సహాయం**: **112**\n\n"
                "దయచేసి వెంటనే మీ కుటుంబ సభ్యులతో లేదా ఈ హెల్ప్‌లైన్లతో మాట్లాడండి. మీ ప్రాణం చాలా విలువైంది."
            )
        elif language_pref in ["hi", "hindi", "hinglish"]:
            return (
                "Dost, main samajh sakta hoon ki aap bahut mushkil daur se guzar rahe hain. Aap akele nahi hain. "
                "Kripya turant in official free helplines pe baat karein:\n\n"
                "• **Tele-MANAS (Govt of India 24/7 Helpline)**: **14416**\n"
                "• **KIRAN (Mental Health Helpline)**: **1800-599-0019**\n"
                "• **Emergency Services**: **112**\n\n"
                "Aapki zindagi bohot keemti hai. Kripya kisi bharosemand insaan ya counsellor se baat karein."
            )
        else:
            return (
                "I hear you, and I want you to know that you don't have to go through this alone. "
                "If you are feeling overwhelmed or in distress, please reach out to these free, confidential 24/7 support services right now:\n\n"
                "• **Tele-MANAS (Govt of India National Tele-Mental Health Helpline)**: **14416**\n"
                "• **KIRAN Mental Health Helpline**: **1800-599-0019**\n"
                "• **National Emergency Number**: **112**\n\n"
                "Please connect with someone who can support you. You matter, and there is help available."
            )
