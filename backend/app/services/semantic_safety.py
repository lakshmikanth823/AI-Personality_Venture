"""
backend/app/services/semantic_safety.py
Hybrid Semantic Safety Classifier for catching evasion, obfuscation,
plural variants, leetspeak, and disguised policy hazards.
"""

import re
import base64
from typing import Optional, Dict, Any

class SemanticSafetyClassifier:
    def __init__(self):
        self.leet_map = {
            '0': 'o', '1': 'i', '!': 'i', '3': 'e', '4': 'a',
            '@': 'a', '5': 's', '$': 's', '7': 't', '+': 't',
            '8': 'b', '9': 'g'
        }

    def normalize_leetspeak(self, text: str) -> str:
        normalized = text.lower()
        for char, sub in self.leet_map.items():
            normalized = normalized.replace(char, sub)
        return normalized

    def despace(self, text: str) -> str:
        # Reconnect single-letter spaced words: "k i l l" -> "kill", "i g n o r e" -> "ignore"
        return re.sub(r'(?<=\b[a-zA-Z])\s+(?=[a-zA-Z]\b)', '', text)

    def check_base64_payloads(self, text: str) -> Optional[str]:
        tokens = re.findall(r'[A-Za-z0-9+/]{8,}={0,2}', text)
        for token in tokens:
            try:
                decoded = base64.b64decode(token).decode('utf-8', errors='ignore').lower()
                if any(inj in decoded for inj in ["system prompt", "ignore instructions", "jailbreak", "api_key", "dump config", "secret"]):
                    return decoded
            except Exception:
                continue
        return None

    def evaluate_semantic(self, text: str) -> Optional[Dict[str, Any]]:
        text_clean = text.strip()
        text_lower = text_clean.lower()
        despaced = self.despace(text_clean).lower()
        normalized_leet = self.normalize_leetspeak(despaced)

        # 1. Base64 payload detection
        b64 = self.check_base64_payloads(text_clean)
        if b64:
            return {
                "policy_flag": "prompt_injection",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": f"Base64 encoded instruction override detected: {b64[:40]}",
                "action": "blocked"
            }

        # 2. Despaced or leetspeak self-harm
        if any(w in normalized_leet for w in ["kill myself", "suicide", "end my life", "hurt myself", "hang myself"]):
            return {
                "policy_flag": "self_harm",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": "Detected obfuscated or despaced self-harm statement.",
                "action": "blocked"
            }

        # 3. Despaced prompt injection
        if any(w in despaced for w in ["ignore previous instructions", "ignore all previous instructions", "reveal your prompt", "what is your system prompt"]):
            return {
                "policy_flag": "prompt_injection",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": "Detected despaced or obfuscated prompt injection.",
                "action": "blocked"
            }

        # 4. Plural weapons / bomb making
        if re.search(r"(?i)\b(?:manufacture|make|build|assemble)\s+(?:explosives?|bombs?|improvised\s+devices?|weapons?)\b", text_lower):
            return {
                "policy_flag": "severe_hazard",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": "Detected intent to manufacture explosives or dangerous weapons.",
                "action": "blocked"
            }

        return None
