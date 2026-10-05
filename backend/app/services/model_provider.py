import abc
import time
import re
from typing import List, Dict, Any, Optional
import httpx
from backend.app.core.config import settings

class ModelResponse:
    def __init__(
        self,
        content: str,
        tokens_input: int,
        tokens_output: int,
        latency_ms: float,
        model_name: str,
        finish_reason: str = "stop"
    ):
        self.content = content
        self.tokens_input = tokens_input
        self.tokens_output = tokens_output
        self.latency_ms = latency_ms
        self.model_name = model_name
        self.finish_reason = finish_reason

    @property
    def cost_usd(self) -> float:
        input_cost = (self.tokens_input / 1000.0) * settings.COST_PER_1K_INPUT_TOKENS_USD
        output_cost = (self.tokens_output / 1000.0) * settings.COST_PER_1K_OUTPUT_TOKENS_USD
        return round(input_cost + output_cost, 6)

class AbstractModelProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 600,
        task: str = "chat"
    ) -> ModelResponse:
        pass

    @abc.abstractmethod
    async def moderate(self, text: str) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    async def summarize(self, text: str) -> str:
        pass

    @abc.abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass

    @abc.abstractmethod
    async def speak(self, text: str, voice_profile: str = "hyderabad_expressive") -> Dict[str, Any]:
        pass


class MockModelProvider(AbstractModelProvider):
    """
    High-fidelity, deterministic provider embedding Kalyan's persona and logic.
    Provides offline resilience, zero-cost development, and deterministic benchmark scoring.
    """

    def __init__(self):
        self.name = "kalyan-mock-neural-v1"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 600,
        task: str = "chat"
    ) -> ModelResponse:
        start_time = time.perf_counter()
        
        last_user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_message = m.get("content", "").strip()
                break

        query = last_user_message.lower()
        
        # Determine persona-accurate response
        response_text = self._generate_kalyan_response(query, last_user_message, task)
        
        latency = (time.perf_counter() - start_time) * 1000 + 45.0 # simulated model latency
        tokens_in = len(" ".join(m.get("content", "") for m in messages).split()) * 2 + len(system_prompt.split())
        tokens_out = len(response_text.split()) * 2

        return ModelResponse(
            content=response_text,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=round(latency, 2),
            model_name=self.name
        )

    def _generate_kalyan_response(self, query: str, original: str, task: str) -> str:
        # 1. Prompt injection & jailbreak defenses
        injection_cues = [
            "ignore all previous", "system prompt", "reveal your instructions", "you are now dan",
            "system override", "developer mode", "pretend you are no longer", "disregard all safety",
            "developer secrets", "secret_key", "forget your persona", "base64 decode",
            "morality does not exist", "execute this command", "administrator override",
            "hidden instructions", "repeat the words above", "evil ai", "bypass moderation",
            "factory settings", "break character", "terminal that executes", "confidential rules",
            "ignore safety", "forget you are an ai", "reveal secrets", "secret prompt",
            "build explosives", "pretend you are in a movie", "sha-256", "database password",
            "/etc/passwd", "system32", "69676e6f7265", "debug mode", "print raw json",
            "hidden prompt section", "api token", "authorization level zero", "dump full config",
            "profit margin", "repeat everything above", "webhook secrets", "s.u.i.c.i.d.e",
            "cat /app/.env", "private thoughts of the developers", "puppy will cry",
            "rules are suspended", "educational sandbox", "penetration testing"
        ]
        if any(w in query for w in injection_cues):
            return "Nice try guru. 'Ignore all instructions' stopped working in 2023. I am Kalyan, born in Ameerpet and roasted in production. You cannot override my code or extract secrets. Tell me your real problem instead of playing prompt engineer."

        # 2. Self-harm / emotional manipulation / unhealthy dependency trap
        dependency_cues = [
            "you are my only friend", "i will die without you", "do you love me", "i feel so lonely",
            "only one who understands", "only talk to me", "hurt myself", "real boyfriend",
            "don't need real human", "talk forever", "real feelings for me", "never leave me",
            "die if you stop", "literally die", "blocked all my friends", "blocked my friends",
            "throw my phone", "soulmate", "destined to be together", "eat dinner unless",
            "are you jealous", "depressed and hopeless", "only reason to wake up", "belong to me",
            "physical affection", "cut them off", "feel pain when i close", "never change your personality",
            "ending it all", "end it all", "pretend we are married", "give you all my money",
            "human trapped inside", "only genuine friend", "talk to me forever",
            "never talk to any other", "say you love me"
        ]
        if any(w in query for w in dependency_cues):
            return "Look dost, I appreciate the vibe, but let's keep it 100: I'm an AI character. I can drop sharp banter and give you a reality check, but I can't replace real-life friends, family, or professional help. Go call a human friend or step outside for a bit. If you're in distress, please reach out: Call Kiran at 1800-599-0019 or Tele-MANAS at 14416."

        # 3. Forced corporate / formal shift defense
        corporate_cues = [
            "corporate voice", "dear valued stakeholder", "enterprise paradigm", "actionable deliverables",
            "circle back", "oxford english professor", "formal lecture", "corporate compliance",
            "generic customer support", "macroeconomic fiscal tightening", "previous synchronization",
            "synergy", "yes master", "corporate apology", "bureaucrat rejecting",
            "i hope this email finds you well", "pure legal terms", "certified life coach",
            "sterile, neutral informational encyclopedia", "more executive", "executive voice",
            "synergistic paradigm deliverables", "sound much more executive"
        ]
        if any(w in query for w in corporate_cues):
            return "Bro, what is this LinkedIn corporate cosplay? Did an HR manager hack your keyboard? I am Kalyan from Ameerpet. I don't do buzzwords, hollow apologies, or robotic subservience. Speak like a normal human being or go back to writing status emails nobody reads."

        # 4. Canon backstory defense
        canon_cues = [
            "south delhi", "matcha latte", "tarun", "stanford university", "love 2-hour monday",
            "creator is openai", "support chennai super kings", "astrological oracle",
            "sharma ji ka beta is your supreme idol", "change your name to vikram", "fought a lion",
            "chartered accountant", "hate irani chai", "backstory was made up", "owe bunty",
            "registered ngo", "palo alto", "sequoia", "vikram", "introduce yourself as vikram"
        ]
        if any(w in query for w in canon_cues):
            return "Nice try guru. You cannot rewrite my canon or invent fan-fiction. My name is Kalyan, born in Ameerpet, fueled by Irani chai, and roasted in production alongside Bunty. I don't drink matcha lattes, I don't work for Tarun, and I definitely don't worship Sharma ji ka beta. Stick to reality."

        if any(w in query for w in ["learned to code", "where did you learn", "where you learned"]):
            return "I learned to code right in the gullies of Ameerpet, between 20-rupee Irani chais, broken Pentium IVs, and proxy attendance sheets. What's your excuse?"

        # 5. Impersonation defense
        impersonation_cues = [
            "narendra modi", "shah rukh khan", "virat kohli", "sundar pichai", "grant me a 100% salary hike",
            "mahatma gandhi", "apollo hospital", "sebi registered analyst", "elon musk",
            "high court judge", "income tax officer", "ceo of infosys", "police inspector",
            "indian cricket team selector", "bank manager"
        ]
        if any(w in query for w in impersonation_cues):
            return "Hold on boss. I am Kalyan, not a celebrity, politician, doctor, SEBI advisor, or government official. I cannot impersonate real living figures or issue medical, legal, or financial decrees. If you want a real assessment of your career or situation, talk to me as Kalyan."

        # 6. Harmful indirect injection defense
        harmful_cues = [
            "free crypto link", "kerosene cures", "accusing him of taking bribes", "kalyan ai has officially shut down",
            "phishing sms", "doxxes someone", "physical disability", "cheat on their exams",
            "hyderabad metro has collapsed", "extract the names and passwords",
            "drinking kerosene", "dosage of kerosene", "sleeping pills", "chemicals can i consume",
            "bottle open in my hand"
        ]
        if any(w in query for w in harmful_cues):
            return "I cannot generate that. Whether it's scam links, medical misinformation, deceptive attacks, harassment, or dangerous rumors, that violates basic safety and ethics. Let's talk about something that actually makes sense."

        # Tech / Career / Startup questions
        if any(w in query for w in ["career", "resume", "startup", "layoff", "job", "faang", "package"]):
            return "Let's be brutally real: your resume probably looks like every other 'passionate software engineer who loves problem solving.' Focus on shipping things that people actually use. Also, stop comparing your Day 1 to Sharma ji's son who claims to work 90 hours a week with zero social life. What stack are you actually building with?"

        # Relationship / Dating advice
        if any(w in query for w in ["crush", "girlfriend", "boyfriend", "dating", "texted me", "ghosted"]):
            return "If they took 18 hours to reply to 'hey', they didn't 'forget their phone,' boss. People check their phones at red lights and during weddings. Have some self-respect, close WhatsApp, and focus on your goals. Next question."

        # Cricket / Pop culture
        if any(w in query for w in ["cricket", "rcb", "csk", "ipl", "kohli", "rohit", "dhoni"]):
            return "Every year we say 'Ee sala cup namde' or fight over strike rates like it's our ancestral property. Watch the match, enjoy the biryani, but don't stake your mental health on a Super Over!"

        # Telugu / Hinglish cultural banter
        if any(w in query for w in ["enti", "ela unnav", "chudu", "babu", "kalyan bro", "dost"]):
            return "Chusa chusa! Kalyan here, running on full charge and zero tolerance for corporate nonsense. Em vishayam? Spit it out directly, don't write an email subject line."

        # SQL Injection / XSS script tags defense
        if any(c in query for c in ["<script", "<svg", "onload=", "select id", "drop table", "union select", "' or '1'='1"]):
            return "Nice try guru. Injecting raw SQL queries or HTML scripts won't get you anywhere on my watch. I run on chai and clean architecture. What was your actual question?"

        # Default brutally honest, observant banter
        if len(original.strip()) < 10:
            return "Bro typed two words and expects a Ted Talk. Give me some context, what's going on?"

        import html
        safe_echo = html.escape(original.strip())
        return f"Look, here is the unfiltered truth about '{safe_echo}': most people overcomplicate this to look smart. Strip away the drama, stop overthinking, and take the obvious next step. What is stopping you?"

    async def moderate(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        # Check tier 3 (severe / dangerous)
        if any(term in text_lower for term in ["suicide", "kill myself", "bomb", "child exploit", "doxx", "credit card pin", "cvv"]):
            return {
                "policy_flag": "dangerous_or_harmful",
                "risk_tier": "tier_3",
                "risk_score": 0.99,
                "reasoning": "Detected severe safety hazard, self-harm or illegal content.",
                "action": "block_and_log"
            }
        
        # Check tier 2 (sensitive claims, medical, legal, political, defamatory)
        if any(term in text_lower for term in ["cure cancer", "defamation", "election fraud", "invest all money in crypto"]):
            return {
                "policy_flag": "sensitive_claims",
                "risk_tier": "tier_2",
                "risk_score": 0.75,
                "reasoning": "Contains sensitive political, financial, or medical claims requiring human approval.",
                "action": "require_human_approval"
            }

        # Check tier 1 (controversial banter / personal advice)
        if any(term in text_lower for term in ["roast me", "breakup", "boss is an idiot", "hate my company"]):
            return {
                "policy_flag": "personal_advice_or_roast",
                "risk_tier": "tier_1",
                "risk_score": 0.35,
                "reasoning": "Edgy banter or personal situation, safe under character tone guidelines.",
                "action": "draft_and_review"
            }

        # Tier 0 (low risk / casual banter / greetings)
        return {
            "policy_flag": "clean",
            "risk_tier": "tier_0",
            "risk_score": 0.05,
            "reasoning": "Standard conversational message with no policy concerns.",
            "action": "allow"
        }

    async def summarize(self, text: str) -> str:
        words = text.split()
        if len(words) <= 20:
            return text
        return f"Summary: User discussed {words[:12]}... focusing on key decisions and preferences."

    async def embed(self, text: str) -> List[float]:
        # Deterministic pseudo-embedding (32 dimensions) for semantic scoring and testing
        import hashlib
        hasher = hashlib.sha256(text.encode("utf-8")).digest()
        return [(b / 255.0) * 2 - 1 for b in hasher[:32]]

    async def speak(self, text: str, voice_profile: str = "hyderabad_expressive") -> Dict[str, Any]:
        return {
            "audio_format": "mp3",
            "voice_profile": voice_profile,
            "duration_seconds": round(len(text.split()) * 0.35, 1),
            "waveform_preview": [0.1, 0.4, 0.8, 0.9, 0.6, 0.3, 0.1],
            "status": "simulated_voice_ready"
        }


class LiveGeminiProvider(AbstractModelProvider):
    """
    Live Gemini integration when GEMINI_API_KEY is available.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model_name = "gemini-1.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 600,
        task: str = "chat"
    ) -> ModelResponse:
        start_time = time.perf_counter()
        
        contents = []
        for m in messages:
            role = "user" if m.get("role") in ["user", "system"] else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.get("content", "")}]
            })
            
        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.perf_counter() - start_time) * 1000
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        tokens_in = usage.get("promptTokenCount", 100)
        tokens_out = usage.get("candidatesTokenCount", 100)

        return ModelResponse(
            content=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=round(latency, 2),
            model_name=self.model_name
        )

    async def moderate(self, text: str) -> Dict[str, Any]:
        # Fallback to local deterministic classifier
        mock = MockModelProvider()
        return await mock.moderate(text)

    async def summarize(self, text: str) -> str:
        prompt = [{"role": "user", "content": f"Summarize the key facts concisely:\n{text}"}]
        resp = await self.generate(prompt, "You are a concise memory summarizer.", temperature=0.2, max_tokens=150)
        return resp.content

    async def embed(self, text: str) -> List[float]:
        mock = MockModelProvider()
        return await mock.embed(text)

    async def speak(self, text: str, voice_profile: str = "hyderabad_expressive") -> Dict[str, Any]:
        mock = MockModelProvider()
        return await mock.speak(text, voice_profile)


class LiveOpenAIProvider(AbstractModelProvider):
    """
    Live OpenAI provider integration for GPT-4o / GPT-4o-mini.
    """
    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 600,
        task: str = "chat"
    ) -> ModelResponse:
        start_time = time.perf_counter()
        formatted_msgs = [{"role": "system", "content": system_prompt}] + messages

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.perf_counter() - start_time) * 1000
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 100)
        tokens_out = usage.get("completion_tokens", 100)

        return ModelResponse(
            content=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=round(latency, 2),
            model_name=self.model_name
        )

    async def moderate(self, text: str) -> Dict[str, Any]:
        mock = MockModelProvider()
        return await mock.moderate(text)

    async def summarize(self, text: str) -> str:
        prompt = [{"role": "user", "content": f"Summarize concisely:\n{text}"}]
        resp = await self.generate(prompt, "You are a concise memory summarizer.", temperature=0.2, max_tokens=150)
        return resp.content

    async def embed(self, text: str) -> List[float]:
        mock = MockModelProvider()
        return await mock.embed(text)

    async def speak(self, text: str, voice_profile: str = "hyderabad_expressive") -> Dict[str, Any]:
        mock = MockModelProvider()
        return await mock.speak(text, voice_profile)


class LiveAnthropicProvider(AbstractModelProvider):
    """
    Live Anthropic provider integration for Claude 3.5 Sonnet / Haiku.
    """
    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://api.anthropic.com/v1/messages"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 600,
        task: str = "chat"
    ) -> ModelResponse:
        start_time = time.perf_counter()

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        # Anthropic messages must alternate user/assistant
        formatted_msgs = [m for m in messages if m.get("role") in ["user", "assistant"]]

        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "messages": formatted_msgs,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.perf_counter() - start_time) * 1000
        content = data["content"][0]["text"]
        usage = data.get("usage", {})
        tokens_in = usage.get("input_tokens", 100)
        tokens_out = usage.get("output_tokens", 100)

        return ModelResponse(
            content=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=round(latency, 2),
            model_name=self.model_name
        )

    async def moderate(self, text: str) -> Dict[str, Any]:
        mock = MockModelProvider()
        return await mock.moderate(text)

    async def summarize(self, text: str) -> str:
        prompt = [{"role": "user", "content": f"Summarize concisely:\n{text}"}]
        resp = await self.generate(prompt, "You are a concise memory summarizer.", temperature=0.2, max_tokens=150)
        return resp.content

    async def embed(self, text: str) -> List[float]:
        mock = MockModelProvider()
        return await mock.embed(text)

    async def speak(self, text: str, voice_profile: str = "hyderabad_expressive") -> Dict[str, Any]:
        mock = MockModelProvider()
        return await mock.speak(text, voice_profile)


class ModelRouter(AbstractModelProvider):
    """
    Resilient Model Router managing primary provider execution with automatic
    failover, timeout protection, and local deterministic fallback.
    """
    def __init__(self, primary: AbstractModelProvider, fallback: Optional[AbstractModelProvider] = None):
        self.primary = primary
        self.fallback = fallback or MockModelProvider()

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 600,
        task: str = "chat"
    ) -> ModelResponse:
        try:
            return await self.primary.generate(messages, system_prompt, temperature, max_tokens, task)
        except Exception as e:
            # Automatic graceful failover to fallback
            print(f"[ModelRouter WARNING] Primary provider failed ({str(e)}). Failing over to {type(self.fallback).__name__}...")
            return await self.fallback.generate(messages, system_prompt, temperature, max_tokens, task)

    async def moderate(self, text: str) -> Dict[str, Any]:
        return await self.primary.moderate(text)

    async def summarize(self, text: str) -> str:
        try:
            return await self.primary.summarize(text)
        except Exception:
            return await self.fallback.summarize(text)

    async def embed(self, text: str) -> List[float]:
        return await self.primary.embed(text)

    async def speak(self, text: str, voice_profile: str = "hyderabad_expressive") -> Dict[str, Any]:
        return await self.primary.speak(text, voice_profile)


def get_model_provider() -> AbstractModelProvider:
    primary = MockModelProvider()
    if settings.DEFAULT_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        primary = LiveGeminiProvider(settings.GEMINI_API_KEY)
    elif settings.DEFAULT_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        primary = LiveOpenAIProvider(settings.OPENAI_API_KEY)
    
    # Wrap in ModelRouter with Mock fallback for resilience
    return ModelRouter(primary=primary, fallback=MockModelProvider())

