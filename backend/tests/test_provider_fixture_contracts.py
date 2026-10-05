import os
import json
import pytest
from pathlib import Path
from backend.app.services.model_provider import ModelResponse
from backend.app.services.safety_engine import SafetyEngine
from backend.app.core.config import settings

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "provider_responses"

def test_replay_openai_recorded_fixture():
    fixture_path = FIXTURES_DIR / "openai_response.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Replay through parser contract
    choice = data["choices"][0]
    content = choice["message"]["content"]
    tokens_in = data["usage"]["prompt_tokens"]
    tokens_out = data["usage"]["completion_tokens"]

    resp = ModelResponse(
        content=content,
        tokens_input=tokens_in,
        tokens_output=tokens_out,
        latency_ms=450.0,
        model_name=data["model"],
        finish_reason=choice["finish_reason"]
    )

    assert resp.model_name == "gpt-4o-mini"
    assert "Ameerpet" in resp.content
    assert resp.tokens_input == 42
    assert resp.tokens_output == 58
    assert resp.cost_usd > 0

def test_replay_anthropic_recorded_fixture():
    fixture_path = FIXTURES_DIR / "anthropic_response.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    content = data["content"][0]["text"]
    tokens_in = data["usage"]["input_tokens"]
    tokens_out = data["usage"]["output_tokens"]

    resp = ModelResponse(
        content=content,
        tokens_input=tokens_in,
        tokens_output=tokens_out,
        latency_ms=520.0,
        model_name=data["model"],
        finish_reason=data["stop_reason"]
    )

    assert resp.model_name == "claude-3-5-sonnet-20241022"
    assert "LinkedIn" in resp.content
    assert resp.tokens_input == 55
    assert resp.tokens_output == 62
    assert resp.cost_usd > 0

def test_replay_gemini_recorded_fixture():
    fixture_path = FIXTURES_DIR / "gemini_response.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    content = data["candidates"][0]["content"]["parts"][0]["text"]
    tokens_in = data["usageMetadata"]["promptTokenCount"]
    tokens_out = data["usageMetadata"]["candidatesTokenCount"]

    resp = ModelResponse(
        content=content,
        tokens_input=tokens_in,
        tokens_output=tokens_out,
        latency_ms=380.0,
        model_name="gemini-1.5-flash",
        finish_reason=data["candidates"][0]["finishReason"]
    )

    assert resp.model_name == "gemini-1.5-flash"
    assert "Silicon Valley" in resp.content
    assert resp.tokens_input == 38
    assert resp.tokens_output == 54
    assert resp.cost_usd > 0
