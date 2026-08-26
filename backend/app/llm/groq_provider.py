import logging
from typing import AsyncGenerator, List, Optional
from groq import AsyncGroq, GroqError

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

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "llama-3.3-70b-versatile"):
        super().__init__(model_name=model_name, api_key=api_key)
        self.client = AsyncGroq(api_key=api_key) if api_key else None

    @property
    def provider_name(self) -> str:
        return "groq"

    def _prepare_messages(self, messages: List[ChatMessage], system_prompt: Optional[str]) -> List[dict]:
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for msg in messages:
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
                reason="GROQ_API_KEY is missing or invalid.",
                actionable_instructions="Set GROQ_API_KEY environment variable in your .env configuration file."
            )

        formatted_msgs = self._prepare_messages(messages, system_prompt)
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted_msgs,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta.content or ""
                    finish_reason = chunk.choices[0].finish_reason
                    yield LLMStreamChunk(delta_text=delta, finish_reason=finish_reason)
        except GroqError as e:
            logger.error(f"Groq API Error: {str(e)}")
            raise LLMException(f"Groq generation failed: {str(e)}", provider_name=self.provider_name) from e

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
                reason="GROQ_API_KEY is missing or invalid.",
                actionable_instructions="Set GROQ_API_KEY environment variable in your .env configuration file."
            )

        formatted_msgs = self._prepare_messages(messages, system_prompt)
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted_msgs,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            choice = response.choices[0]
            usage = response.usage
            return LLMResponse(
                content=choice.message.content or "",
                finish_reason=choice.finish_reason or "stop",
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                provider_name=self.provider_name,
                model_name=self.model_name,
            )
        except GroqError as e:
            logger.error(f"Groq API Error: {str(e)}")
            raise LLMException(f"Groq complete generation failed: {str(e)}", provider_name=self.provider_name) from e

    async def check_health(self) -> ProviderHealthStatus:
        if not self.api_key:
            return ProviderHealthStatus(
                is_available=False,
                provider_name=self.provider_name,
                current_model=self.model_name,
                is_local=False,
                available_models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
                error_message="GROQ_API_KEY not found in environment settings."
            )
        try:
            # Quick lightweight check
            await self.client.models.list()
            return ProviderHealthStatus(
                is_available=True,
                provider_name=self.provider_name,
                current_model=self.model_name,
                is_local=False,
                available_models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            )
        except Exception as e:
            return ProviderHealthStatus(
                is_available=False,
                provider_name=self.provider_name,
                current_model=self.model_name,
                is_local=False,
                available_models=[],
                error_message=f"Health probe failed: {str(e)}"
            )
