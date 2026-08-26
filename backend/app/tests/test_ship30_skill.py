import pytest
from app.skills.ship30 import Ship30EssayPipeline, EssayOutputSchema

def test_ship30_essay_schema_validation():
    valid_payload = {
        "title": "How to Build High-Velocity Product Teams",
        "hook": "Most startup teams fail because they optimize for speed instead of velocity.",
        "sections": [
            {"header": "1. Define Clear Alignment", "content": "One key decision saves ten meetings..."},
            {"header": "2. Measure Output Metrics", "content": "Track lead indicators, not lag indicators..."},
            {"header": "3. Empower Feature Owners", "content": "Give engineers full ownership of metrics..."}
        ],
        "conclusion": "Focus on velocity today to build enduring value."
    }
    schema = EssayOutputSchema(**valid_payload)
    assert schema.title == "How to Build High-Velocity Product Teams"
    assert len(schema.sections) == 3

def test_ship30_1_3_1_formatting_validator():
    pipeline = Ship30EssayPipeline()
    sample_text = "Hook line here.\n\nBody paragraph line 1.\nBody paragraph line 2.\nBody paragraph line 3.\n\nTakeaway summary line."
    is_valid = pipeline.validate_1_3_1_structure(sample_text)
    assert is_valid is True
