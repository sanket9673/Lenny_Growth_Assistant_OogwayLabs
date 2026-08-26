from typing import List, AsyncGenerator
from app.llm.base import ChatMessage, BaseLLMProvider
from app.llm.factory import llm_factory

class LLMWrapper:
    def __init__(self, provider_instance: BaseLLMProvider, model: str):
        self.provider = provider_instance
        self.provider.model_name = model

    async def astream(self, messages: List[ChatMessage]) -> AsyncGenerator[str, None]:
        system_prompt = None
        other_messages = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                other_messages.append(msg)
        
        async for chunk in self.provider.generate_stream(messages=other_messages, system_prompt=system_prompt):
            if chunk.delta_text:
                yield chunk.delta_text

class LLMFactory:
    @classmethod
    def get_llm(cls, provider: str, model: str) -> LLMWrapper:
        provider_instance = llm_factory.get_provider(requested_provider=provider)
        return LLMWrapper(provider_instance, model)
