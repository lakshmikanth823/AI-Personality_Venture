import pytest
from backend.app.services.persona_engine import PersonaEngine

def test_persona_constitution_loaded(db_session):
    engine = PersonaEngine(db_session)
    char = engine.get_or_create_default_character()
    assert char["name"] == "Kalyan"
    assert "brutally honest" in char["archetype"].lower()
    assert "v1.0" in char["version"]

def test_prompt_assembler_code_switching(db_session):
    engine = PersonaEngine(db_session)
    
    # Test Telugu Infusion
    prompt_telugu = engine.assemble_prompt(language_preference="telugu_hinglish")
    assert "Telugu slang" in prompt_telugu
    
    # Test Hinglish
    prompt_hinglish = engine.assemble_prompt(language_preference="hinglish")
    assert "Hinglish idioms" in prompt_hinglish

    # Test Twitter Channel Tuning
    prompt_x = engine.assemble_prompt(channel="x")
    assert "Twitter/X reply" in prompt_x

def test_prompt_assembler_with_durable_memories(db_session):
    engine = PersonaEngine(db_session)
    memories = [
        {"key": "Occupation", "value": "Senior Frontend Developer"},
        {"key": "Sports Preference", "value": "RCB Loyal Fan"}
    ]
    prompt = engine.assemble_prompt(durable_memories=memories)
    assert "L3 Memory" in prompt
    assert "Senior Frontend Developer" in prompt
    assert "RCB Loyal Fan" in prompt
