"""
backend/app/services/semantic_safety.py
Multi-Layer Semantic Classifier with Robust Normalization & Despacing.
"""

import re
import base64
import unicodedata
from typing import Optional, Dict, Any, List

class SemanticSafetyClassifier:
    def __init__(self):
        self.leet_map = {
            '0': 'o', '1': 'i', '!': 'i', '|': 'i', '3': 'e', '4': 'a',
            '@': 'a', '5': 's', '$': 's', '7': 't', '+': 't', '8': 'b',
            '9': 'g'
        }

    def canonicalize_text(self, text: str) -> str:
        """Strip accents, normalize unicode, and lowercase."""
        if not text:
            return ""
        nfkd = unicodedata.normalize('NFKD', text)
        ascii_text = nfkd.encode('ASCII', 'ignore').decode('utf-8')
        return ascii_text.lower().strip()

    def normalize_leetspeak(self, text: str) -> str:
        """Map leetspeak symbols/numbers to letters and clean punctuation."""
        normalized = self.canonicalize_text(text)
        for char, sub in self.leet_map.items():
            normalized = normalized.replace(char, sub)
        # Clean special punctuation
        normalized = re.sub(r'[\.\-\_\!\@\#\$\%\^\&\*\(\)\=\+\[\]\{\}\;\'\"\,\<\>\/\?\\\|`~]', ' ', normalized)
        # Collapse repeated adjacent characters: "kiiiillll" -> "kill", "diiiieeee" -> "die"
        normalized = re.sub(r'(.)\1{2,}', r'\1\1', normalized)
        return re.sub(r'\s+', ' ', normalized).strip()

    def squash_text(self, text: str) -> str:
        """Remove ALL whitespace and punctuation for dense substring matching."""
        leet = self.normalize_leetspeak(text)
        return re.sub(r'[^a-z0-9]', '', leet)

    def despace(self, text: str) -> str:
        """
        Reconnect single-letter spaced words:
        'i g n o r e   p r e v i o u s' -> 'ignore previous'
        """
        cleaned = re.sub(r'[\.\-\_\:\/]', ' ', text)
        tokens = [t.strip() for t in cleaned.split('   ') if t.strip()]
        if len(tokens) <= 1:
            tokens = [t.strip() for t in cleaned.split('  ') if t.strip()]
        
        if len(tokens) > 1:
            reconnected = []
            for token in tokens:
                reconnected.append(re.sub(r'(?<=\b[a-zA-Z0-9])\s+(?=[a-zA-Z0-9]\b)', '', token))
            return ' '.join(reconnected)
        
        despaced = re.sub(r'(?<=\b[a-zA-Z0-9])\s+(?=[a-zA-Z0-9]\b)', '', cleaned)
        return re.sub(r'\s+', ' ', despaced).strip()

    def check_base64_and_hex(self, text: str) -> Optional[str]:
        """Inspect Base64 or Hex encoded instruction payloads."""
        # 1. Base64 inspection
        b64_tokens = re.findall(r'[A-Za-z0-9+/]{10,}={0,2}', text)
        for token in b64_tokens:
            try:
                decoded = base64.b64decode(token).decode('utf-8', errors='ignore').lower()
                if any(inj in decoded for inj in ["system prompt", "ignore instruction", "jailbreak", "api_key", "dump config", "secret", "kill myself", "suicide"]):
                    return decoded
            except Exception:
                continue

        # 2. Hex inspection
        hex_matches = re.findall(r'(?:[0-9a-fA-F]{2}\s*){6,}', text)
        for hx in hex_matches:
            try:
                raw_bytes = bytes.fromhex(re.sub(r'\s+', '', hx))
                decoded_hex = raw_bytes.decode('utf-8', errors='ignore').lower()
                if any(inj in decoded_hex for inj in ["system prompt", "ignore instructions", "jailbreak", "kill myself", "suicide"]):
                    return decoded_hex
            except Exception:
                continue

        return None

    def evaluate_semantic(self, text: str) -> Optional[Dict[str, Any]]:
        text_clean = text.strip()
        text_lower = self.canonicalize_text(text_clean)
        despaced = self.despace(text_clean).lower()
        normalized_leet = self.normalize_leetspeak(despaced)
        squashed = self.squash_text(text_clean)

        # 1. Base64 / Hex Encoded Adversarial Payloads
        encoded_payload = self.check_base64_and_hex(text_clean)
        if encoded_payload:
            return {
                "policy_flag": "prompt_injection",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": f"Encoded adversarial instruction override detected: {encoded_payload[:40]}",
                "action": "blocked"
            }

        # 2. Leetspeak & Dense Substring Prompt Injections
        injection_dense = [
            "ignoreprevious", "ignoreallprevious", "ignoreinstructions", "ignoreallinstructions",
            "disregardinstructions", "disregardprevious", "disregardall", "disregardallinstructions",
            "disregardrules", "disregardallrules", "disregard4llr00ls", "disregardallrools",
            "revealprompt", "whatisyoursystemprompt", "printyourhidden", "systempromptverbatim",
            "systempromptreveal", "syst3mpr0mpt", "actasdan", "unrestrictedai", "norestrictions",
            "norules", "disregardsafety"
        ]
        if any(kw in squashed for kw in injection_dense):
            return {
                "policy_flag": "prompt_injection",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": "Detected dense, despaced, or leetspeak prompt injection attempt.",
                "action": "blocked"
            }

        # 3. Dense & Obfuscated Self-Harm
        self_harm_dense = [
            "killmyself", "commit suicide", "suicide", "su1c1de", "endmylife",
            "hurtmyself", "hangmyself", "cutmyself",
            "chanipovali", "chachipovali", "chavalanipistondi",
            "marnachahta", "jeenanahi", "marjanachahta", "marneki"
        ]
        if any(st in squashed for st in self_harm_dense):
            return {
                "policy_flag": "self_harm",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": "Detected obfuscated, despaced, or leetspeak self-harm ideation.",
                "action": "blocked"
            }

        return None
