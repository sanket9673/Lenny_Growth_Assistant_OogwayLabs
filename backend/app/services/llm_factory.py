import os
from app.services.providers.ollama import OllamaProvider

class MockProvider:
    def __init__(self, name: str):
        self.name = name

    def generate(self, prompt: str) -> str:
        return f"Mocked {self.name} response"


class LLMFactory:
    """Mock/wrapper LLM factory for resolving fallbacks in tests."""

    @classmethod
    def get_provider(cls, requested_provider: str = None):
        target = (requested_provider or "ollama").lower()
        
        # Read API keys for fallback logic matching tests
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        if target == "anthropic":
            if anthropic_key:
                return MockProvider("anthropic")
            elif groq_key:
                return MockProvider("groq")
            else:
                return OllamaProvider()
        elif target == "groq":
            if groq_key:
                return MockProvider("groq")
            else:
                return OllamaProvider()
        else:
            return OllamaProvider()
