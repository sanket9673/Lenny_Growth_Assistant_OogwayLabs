import json
import logging
import httpx
from typing import AsyncGenerator, List, Optional

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

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3.2"):
        super().__init__(model_name=model_name, base_url=base_url.rstrip("/"))

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _prepare_payload(self, messages: List[ChatMessage], system_prompt: Optional[str], temperature: float, stream: bool) -> dict:
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            msgs.append({"role": m.role, "content": m.content})

        return {
            "model": self.model_name,
            "messages": msgs,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }

    async def generate_stream(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        url = f"{self.base_url}/api/chat"
        payload = self._prepare_payload(messages, system_prompt, temperature, stream=True)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise ProviderUnavailableException(
                            provider_name=self.provider_name,
                            reason=f"Ollama returned HTTP status {response.status_code}.",
                            actionable_instructions="Verify Ollama service is running (`ollama serve`) and model is pulled (`ollama pull llama3.2`)."
                        )
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            message_chunk = data.get("message", {}).get("content", "")
                            done = data.get("done", False)
                            yield LLMStreamChunk(
                                delta_text=message_chunk,
                                finish_reason="stop" if done else None
                            )
        except (httpx.ConnectError, httpx.HTTPError) as e:
            logger.error(f"Ollama connection error: {str(e)}")
            raise ProviderUnavailableException(
                provider_name=self.provider_name,
                reason=f"Failed to connect to Ollama endpoint at {self.base_url}.",
                actionable_instructions="Ensure Ollama is installed and running locally via command: `ollama serve`."
            ) from e

    async def generate_complete(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        url = f"{self.base_url}/api/chat"
        payload = self._prepare_payload(messages, system_prompt, temperature, stream=False)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    raise LLMException(f"Ollama returned error status: {res.status_code}", provider_name=self.provider_name)
                
                data = res.json()
                content = data.get("message", {}).get("content", "")
                prompt_eval = data.get("prompt_eval_count", 0)
                eval_count = data.get("eval_count", 0)

                return LLMResponse(
                    content=content,
                    finish_reason="stop",
                    input_tokens=prompt_eval,
                    output_tokens=eval_count,
                    provider_name=self.provider_name,
                    model_name=self.model_name
                )
        except (httpx.ConnectError, httpx.HTTPError) as e:
            raise ProviderUnavailableException(
                provider_name=self.provider_name,
                reason=f"Cannot reach Ollama at {self.base_url}",
                actionable_instructions="Execute `ollama serve` and verify port 11434 is open."
            ) from e

    async def check_health(self) -> ProviderHealthStatus:
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    models_data = res.json().get("models", [])
                    model_names = [m.get("name") for m in models_data if "name" in m]
                    
                    # Auto-select the first available pulled model if the default is not pulled
                    if model_names and self.model_name not in model_names:
                        # Try to find a match without tag, or just use the first available
                        base_names = [name.split(":")[0] for name in model_names]
                        if self.model_name.split(":")[0] in base_names:
                            idx = base_names.index(self.model_name.split(":")[0])
                            self.model_name = model_names[idx]
                        else:
                            self.model_name = model_names[0]

                    return ProviderHealthStatus(
                        is_available=True,
                        provider_name=self.provider_name,
                        current_model=self.model_name,
                        is_local=True,
                        available_models=model_names
                    )
                else:
                    return ProviderHealthStatus(
                        is_available=False,
                        provider_name=self.provider_name,
                        current_model=self.model_name,
                        is_local=True,
                        error_message=f"Ollama endpoint responded with HTTP status {res.status_code}"
                    )
        except Exception as e:
            return ProviderHealthStatus(
                is_available=False,
                provider_name=self.provider_name,
                current_model=self.model_name,
                is_local=True,
                error_message=f"Connection to local Ollama daemon failed: {str(e)}"
            )
