import json
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.llm.factory import llm_factory
from app.llm.base import ChatMessage, ProviderHealthStatus, ProviderUnavailableException
from app.llm.context import ContextBudgetManager

router = APIRouter(prefix="/models", tags=["LLM Models & Providers"])
context_manager = ContextBudgetManager()

class ProviderMatrixResponse(BaseModel):
    active_provider: str
    providers: List[ProviderHealthStatus]

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: Optional[str] = Field(default="You are an expert AI growth assistant for product managers.")
    provider: Optional[str] = Field(default=None, description="Requested provider ('groq', 'anthropic', 'ollama')")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048)

@router.get("/providers", response_model=ProviderMatrixResponse)
async def get_provider_health_matrix():
    """Pings all LLM providers and returns real-time availability status matrix."""
    statuses = []
    providers_dict = llm_factory._providers

    for name, provider in providers_dict.items():
        status = await provider.check_health()
        statuses.append(status)

    try:
        active = (await llm_factory.get_healthy_provider_or_raise()).provider_name
    except ProviderUnavailableException:
        active = "none"

    return ProviderMatrixResponse(
        active_provider=active,
        providers=statuses
    )

@router.post("/chat/stream")
async def stream_chat_completion(request: ChatCompletionRequest):
    """Unified Server-Sent Events (SSE) streaming chat endpoint across any active provider."""
    try:
        provider = await llm_factory.get_healthy_provider_or_raise(request.provider)
        trimmed_messages, _ = context_manager.truncate_messages(
            messages=request.messages,
            system_prompt=request.system_prompt,
            model_name=provider.model_name,
            reserved_completion_tokens=request.max_tokens,
        )

        async def event_generator():
            try:
                stream = provider.generate_stream(
                    messages=trimmed_messages,
                    system_prompt=request.system_prompt,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
                async for chunk in stream:
                    payload = {"delta": chunk.delta_text, "finish_reason": chunk.finish_reason}
                    yield f"data: {json.dumps(payload)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as stream_err:
                err_payload = {"error": str(stream_err)}
                yield f"data: {json.dumps(err_payload)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except ProviderUnavailableException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM streaming error: {str(e)}")
