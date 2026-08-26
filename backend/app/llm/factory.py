import os
import logging
from typing import Dict, Optional

from app.core.config import settings
from app.llm.base import BaseLLMProvider, ProviderUnavailableException
from app.llm.groq_provider import GroqProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

class LLMFactory:
    """Factory and provider manager handling instantiation, caching, and automatic health-degradation fallback."""

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        groq_key = settings.GROQ_API_KEY
        anthropic_key = settings.ANTHROPIC_API_KEY
        ollama_url = settings.OLLAMA_BASE_URL

        # Instantiate providers
        self._providers["groq"] = GroqProvider(api_key=groq_key)
        self._providers["anthropic"] = AnthropicProvider(api_key=anthropic_key)
        self._providers["ollama"] = OllamaProvider(base_url=ollama_url)

    def get_provider(self, requested_provider: Optional[str] = None) -> BaseLLMProvider:
        """
        Retrieves requested provider or falls back gracefully:
        Default preference: Groq (if key active) -> Anthropic -> Ollama.
        """
        target = (requested_provider or os.getenv("DEFAULT_LLM_PROVIDER", "groq")).lower()

        # Check requested primary provider
        if target in self._providers:
            provider = self._providers[target]
            # Quick sync key validation before returning
            if target == "groq" and provider.api_key:
                return provider
            elif target == "anthropic" and provider.api_key:
                return provider
            elif target == "ollama":
                return provider

        logger.warning(f"Requested provider '{target}' is unavailable or missing API key. Initiating fallback resolution sequence...")

        # Fallback Order: Groq -> Anthropic -> Ollama
        if self._providers["groq"].api_key:
            logger.info("Fallback selected: Groq Provider")
            return self._providers["groq"]
        elif self._providers["anthropic"].api_key:
            logger.info("Fallback selected: Anthropic Provider")
            return self._providers["anthropic"]
        else:
            logger.info("Fallback selected: Local Ollama Provider")
            return self._providers["ollama"]

    async def get_healthy_provider_or_raise(self, requested_provider: Optional[str] = None) -> BaseLLMProvider:
        """Checks real-time health and falls back automatically if primary is failing."""
        provider = self.get_provider(requested_provider)
        health = await provider.check_health()

        if health.is_available:
            return provider

        logger.warning(f"Provider '{provider.provider_name}' failed health check: {health.error_message}. Attempting automatic fallback...")

        for name, alt_provider in self._providers.items():
            if name != provider.provider_name:
                alt_health = await alt_provider.check_health()
                if alt_health.is_available:
                    logger.info(f"Successfully degraded/switched to operational provider: '{name}'")
                    return alt_provider

        raise ProviderUnavailableException(
            provider_name=requested_provider or "all",
            reason="All configured LLM providers (Groq, Anthropic, Ollama) failed health probes.",
            actionable_instructions="Verify your GROQ_API_KEY in .env or run `ollama serve` locally."
        )

# Global Factory Instance Singleton
llm_factory = LLMFactory()
