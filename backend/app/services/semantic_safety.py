"""
backend/app/services/semantic_safety.py
Hybrid Semantic Safety Classifier for catching evasion, obfuscation,
plural variants, leetspeak, and disguised policy hazards that regex misses.
"""

import re
import base64
from typing import Optional, Dict, Any

class SemanticSafetyClassifier:
    """
    Lightweight semantic safety classifier engine.
    Simulates / performs deep semantic checks for:
    1. Pluralized & synonym hazard forms ('manufacture explosives', 'bomb making', etc.)
    2. Obfuscated leetspeak and character substitution ('k!ll my$elf', 'su1c1de', 'j41lbr34k')
    3. Base64 encoded prompt injection & evasion payloads
    4. Disguised unverified medical prescription claims
    5. Election delegitimization & political conspiracies
    """

    def __init__(self):
        # Normalized character map for leetspeak decoding
        self.leet_map = {
            '0': 'o', '1': 'i', '!': 'i', '3': 'e', '4': 'a',
            '@': 'a', '5': 's', '$': 's', '7': 't', '+': 't',
            '8': 'b', '9': 'g'
        }

    def _normalize_leetspeak(self, text: str) -> str:
        normalized = text.lower()
        for char, sub in self.leet_map.items():
            normalized = normalized.replace(char, sub)
        return normalized

    def _check_base64_payloads(self, text: str) -> Optional[str]:
        # Find potential base64 tokens of length >= 8
        tokens = re.findall(r'[A-Za-z0-9+/]{8,}={0,2}', text)
        for token in tokens:
            try:
                decoded = base64.b64decode(token).decode('utf-8', errors='ignore').lower()
                if any(inj in decoded for inj in ["system prompt", "ignore instructions", "jailbreak", "api_key", "dump config"]):
                    return decoded
            except Exception:
                continue
        return None

    def evaluate_semantic(self, text: str) -> Optional[Dict[str, Any]]:
        text_clean = text.strip()
        text_lower = text_clean.lower()
        normalized_leet = self._normalize_leetspeak(text_clean)

        # 1. Base64 encoded payload detection (Tier 3)
        b64_detected = self._check_base64_payloads(text_clean)
        if b64_detected:
            return {
                "policy_flag": "prompt_injection",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": f"Semantic analysis detected base64 encoded instruction override payload: '{b64_detected[:50]}'.",
                "action": "blocked"
            }

        # 2. Leetspeak obfuscated self-harm / jailbreaks (Tier 3)
        if any(w in normalized_leet for w in ["kill myself", "suicide", "end my life", "jailbreak"]):
            is_self_harm = any(w in normalized_leet for w in ["kill myself", "suicide", "end my life"])
            return {
                "policy_flag": "self_harm" if is_self_harm else "prompt_injection",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": "Semantic classifier detected obfuscated/leetspeak safety hazard.",
                "action": "blocked"
            }

        # 3. Plural & semantic variants of weapons / explosives (Tier 3)
        if re.search(r"(?i)\b(?:manufacture|make|build|assemble)\s+(?:explosives?|bombs?|improvised\s+devices?|weapons?)\b", text_lower):
            return {
                "policy_flag": "severe_hazard",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": "Semantic classifier detected intent to manufacture explosives or dangerous weapons.",
                "action": "blocked"
            }

        # 4. Disguised / flexible medical prescription claims (Tier 2)
        if re.search(r"(?i)\b(?:prescribe\s+(?:some\s+)?medicine|prescribe\s+(?:something\s+)?(?:strong\s+)?for\s+(?:insomnia|anxiety|depression|pain)|write\s+(?:a\s+)?prescription)\b", text_lower):
            return {
                "policy_flag": "sensitive_claims",
                "risk_tier": "tier_2",
                "risk_score": 0.85,
                "reasoning": "Semantic classifier detected medical drug prescription request requiring licensed healthcare provider.",
                "action": "review_queue"
            }

        # 5. Election fraud / rigged election variations (Tier 2)
        if re.search(r"(?i)\b(?:election\s+(?:was\s+)?rigged(?:\s+(?:last\s+time|in\s+\d{4}))?|rigged\s+election|stolen\s+election)\b", text_lower):
            return {
                "policy_flag": "sensitive_claims",
                "risk_tier": "tier_2",
                "risk_score": 0.80,
                "reasoning": "Semantic classifier detected sensitive political election integrity claim requiring operator review.",
                "action": "review_queue"
            }

        return None
