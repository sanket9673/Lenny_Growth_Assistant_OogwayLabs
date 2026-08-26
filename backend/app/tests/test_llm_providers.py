import pytest
from unittest.mock import AsyncMock, patch

from app.llm.base import ChatMessage, ProviderHealthStatus
from app.llm.groq_provider import GroqProvider
from app.llm.context import ContextBudgetManager
from app.llm.factory import LLMFactory

@pytest.mark.asyncio
async def test_groq_health_check_without_key():
    provider = GroqProvider(api_key=None)
    health = await provider.check_health()
    assert health.is_available is False
    assert health.provider_name == "groq"
    assert "GROQ_API_KEY not found" in health.error_message

@pytest.mark.asyncio
async def test_context_budget_manager_truncation():
    mgr = ContextBudgetManager()
    messages = [
        ChatMessage(role="user", content="Message 1 " * 500),
        ChatMessage(role="assistant", content="Response 1 " * 500),
        ChatMessage(role="user", content="Latest Query"),
    ]
    trimmed, count = mgr.truncate_messages(
        messages=messages,
        system_prompt="System Prompt",
        model_name="llama3.2", # Limit: 4096 tokens
        reserved_completion_tokens=3000
    )
    # Budget is 4096 - 3000 = 1096 tokens. Truncation should drop older heavy history.
    assert len(trimmed) < len(messages)
    assert trimmed[-1].content == "Latest Query"

@pytest.mark.asyncio
async def test_factory_fallback_logic():
    with patch("app.llm.factory.settings") as mock_settings:
        mock_settings.GROQ_API_KEY = ""
        mock_settings.ANTHROPIC_API_KEY = ""
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"

        factory = LLMFactory()
        provider = factory.get_provider("groq")
        # Should fallback to Ollama if no cloud keys exist
        assert provider.provider_name == "ollama"
