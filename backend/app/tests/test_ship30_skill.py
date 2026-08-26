import pytest
import asyncio
from app.skills.ship30.schema import Ship30Outline, SectionOutline, Ship30EssayDraft, Ship30SectionDraft
from app.skills.ship30.formatting import count_words, enforce_131_cadence, validate_ship30_format
from app.skills.ship30.planner import Ship30Planner
from app.skills.ship30.polisher import Ship30Polisher
from app.skills.ship30.pipeline import Ship30SkillEngine
from app.agents.router import SkillRouter
from app.api.v1.endpoints.chat import DummyLLMFactory


@pytest.fixture
def llm_factory():
    return DummyLLMFactory()


@pytest.fixture
def mock_context():
    return [
        {"guest_name": "Elena Verna", "content": "Retention is key to B2B growth loops."},
        {"guest_name": "Brian Balfour", "content": "Product market fit requires channel fit."}
    ]


@pytest.mark.asyncio
async def test_ship30_outline_generation(llm_factory, mock_context):
    planner = Ship30Planner(llm_factory)
    outline = await planner.generate_outline("How to build retention loops", mock_context)
    
    assert isinstance(outline, Ship30Outline)
    assert len(outline.sections) == 4
    assert outline.total_target_words == 1250
    assert outline.hook_attention != ""


def test_131_formatting_rules():
    raw_text = (
        "Retention is the ultimate driver of sustainable product growth. "
        "Without retention, acquisition spend is wasted. "
        "Top growth leaders prioritize activation metrics above top-of-funnel acquisition. "
        "They build explicit habit loops into the onboarding flow. "
        "This ensures long-term compounding LTV."
    )
    formatted = enforce_131_cadence(raw_text)
    
    assert "\n\n" in formatted
    assert "**This ensures long-term compounding LTV.**" in formatted


@pytest.mark.asyncio
async def test_ship30_word_count_compliance(llm_factory):
    polisher = Ship30Polisher(llm_factory)
    
    # Create draft section with high word count simulation
    sec_content = "Word " * 280 + " [Elena Verna, Episode 10]."
    sections = [
        Ship30SectionDraft(
            section_index=i,
            title=f"Section {i} Title",
            raw_text=sec_content,
            word_count=count_words(sec_content),
            citations_included=["Elena Verna"]
        )
        for i in range(1, 5)
    ]
    
    draft = Ship30EssayDraft(
        topic="Retention Frameworks",
        hook_text="Hook text line 1\n\nHook line 2\n\nHook line 3\n\n**Actionable:** Do this.",
        sections=sections,
        conclusion_framework="**Step 1:** Measure retention.\n**Step 2:** Optimize activation.",
        total_word_count=1200
    )
    
    result = await polisher.polish_and_assemble(draft)
    
    assert result.word_count >= 1100
    assert result.word_count <= 1600
    assert len(result.citations) > 0


@pytest.mark.asyncio
async def test_skill_router_intent_detection(llm_factory):
    router = SkillRouter(llm_factory)
    
    # Keyword detection
    decision_kw = await router.route("Write an essay on PLG growth models")
    assert decision_kw.selected_skill == "ship30"
    assert decision_kw.confidence >= 0.9
    
    # Skill override flag
    decision_override = await router.route("Give me quick tips", skill_override="ship30")
    assert decision_override.selected_skill == "ship30"
    assert decision_override.confidence == 1.0
    
    # Standard Q&A route
    decision_qa = await router.route("What is churn rate?")
    assert decision_qa.selected_skill in ["standard_qa", "ship30"]
