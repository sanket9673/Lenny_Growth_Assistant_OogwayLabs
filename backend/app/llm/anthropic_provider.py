import logging
from typing import AsyncGenerator, List, Optional
from anthropic import AsyncAnthropic, APIError

from app.llm.base import (
    BaseLLMProvider,
    ChatMessage,
    LLMResponse,
    LLMStreamChunk,
    ProviderHealthStatus,
    ProviderUnavailableException,
    LLMException,
)

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "claude-3-5-sonnet-20241022"):
        super().__init__(model_name=model_name, api_key=api_key)
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _prepare_messages(self, messages: List[ChatMessage]):
        formatted = []
        for msg in messages:
            if msg.role != "system":
                formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    async def generate_stream(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        if not self.client:
            raise ProviderUnavailableException(
                provider_name=self.provider_name,
                reason="ANTHROPIC_API_KEY is missing.",
                actionable_instructions="Set ANTHROPIC_API_KEY environment variable in your .env file."
            )

        formatted_msgs = self._prepare_messages(messages)
        kw_args = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kw_args["system"] = system_prompt

        try:
            async with self.client.messages.stream(**kw_args) as stream:
                async for text in stream.text_stream:
                    yield LLMStreamChunk(delta_text=text)
        except APIError as e:
            logger.error(f"Anthropic API Error: {str(e)}")
            raise LLMException(f"Anthropic streaming failed: {str(e)}", provider_name=self.provider_name) from e

    async def generate_complete(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if not self.client:
            raise ProviderUnavailableException(
                provider_name=self.provider_name,
                reason="ANTHROPIC_API_KEY is missing.",
                actionable_instructions="Set ANTHROPIC_API_KEY environment variable in your .env file."
            )

        formatted_msgs = self._prepare_messages(messages)
        kw_args = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kw_args["system"] = system_prompt

        try:
            res = await self.client.messages.create(**kw_args)
            content_text = "".join([block.text for block in res.content if hasattr(block, "text")])
            return LLMResponse(
                content=content_text,
                finish_reason=res.stop_reason or "stop",
                input_tokens=res.usage.input_tokens if res.usage else 0,
                output_tokens=res.usage.output_tokens if res.usage else 0,
                provider_name=self.provider_name,
                model_name=self.model_name,
            )
        except APIError as e:
            logger.error(f"Anthropic API Error: {str(e)}")
            raise LLMException(f"Anthropic complete failed: {str(e)}", provider_name=self.provider_name) from e

    async def check_health(self) -> ProviderHealthStatus:
        if not self.api_key:
            return ProviderHealthStatus(
                is_available=False,
                provider_name=self.provider_name,
                current_model=self.model_name,
                is_local=False,
                available_models=["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
                error_message="ANTHROPIC_API_KEY not configured."
            )
        try:
            # Dry run test ping
            await self.client.messages.create(
                model=self.model_name,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}]
            )
            return ProviderHealthStatus(
                is_available=True,
                provider_name=self.provider_name,
                current_model=self.model_name,
                is_local=False,
                available_models=["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
            )
        except Exception as e:
            return ProviderHealthStatus(
                is_available=False,
                provider_name=self.provider_name,
                current_model=self.model_name,
                is_local=False,
                available_models=[],
                error_message=f"Health check failed: {str(e)}"
            )
