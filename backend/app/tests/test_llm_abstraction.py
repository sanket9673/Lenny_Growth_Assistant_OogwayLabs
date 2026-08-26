import pytest
from unittest.mock import patch
from app.services.llm_factory import LLMFactory

def test_llm_provider_fallback_on_missing_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "mock_groq_key")
    provider = LLMFactory.get_provider(requested_provider="anthropic")
    # Fallback logic should fallback to Groq or Ollama when Anthropic API Key is missing
    assert provider.name in ["groq", "ollama"]

@patch("app.services.providers.ollama.OllamaProvider.generate")
def test_ollama_local_execution(mock_generate):
    mock_generate.return_value = "Mocked Ollama response text"
    provider = LLMFactory.get_provider(requested_provider="ollama")
    response = provider.generate(prompt="Test prompt")
    assert response == "Mocked Ollama response text"
    mock_generate.assert_called_once()
