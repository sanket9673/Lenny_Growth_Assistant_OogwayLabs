import json
import asyncio
from typing import AsyncGenerator
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud import crud_session
from app.rag.retriever import TranscriptRetriever
from app.rag.prompt import build_grounded_system_prompt, REFUSAL_RESPONSE
from app.rag.llm_factory import LLMFactory
from app.rag.budget_manager import ContextBudgetManager

router = APIRouter()


class ChatStreamRequest(BaseModel):
    session_id: UUID
    message: str
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/stream")
async def chat_stream(
    payload: ChatStreamRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Validate session
    session = await crud_session.get_session(db, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Persist user message
    await crud_session.add_message(
        db, session_id=payload.session_id, role="user", content=payload.message
    )

    # 3. Fetch past session history for multi-turn context
    past_messages = await crud_session.get_session_messages(db, payload.session_id, limit=10)

    # 4. Perform Grounded Retrieval
    retriever = TranscriptRetriever(db)
    retrieved_chunks, has_context = await retriever.retrieve_relevant_chunks(
        query=payload.message, top_k=5, distance_threshold=0.45
    )

    citations = [chunk.to_citation() for chunk in retrieved_chunks]

    async def event_generator() -> AsyncGenerator[str, None]:
        # Stream Citations Event first
        yield format_sse("citation", {"citations": citations})

        accumulated_tokens = []

        if not has_context:
            # Empty context fallback
            refusal_msg = REFUSAL_RESPONSE
            yield format_sse("token", {"token": refusal_msg})
            accumulated_tokens.append(refusal_msg)
        else:
            # Build Grounded System Prompt
            system_prompt = build_grounded_system_prompt(retrieved_chunks)

            # Context budget management
            budget_manager = ContextBudgetManager(max_tokens=4000)
            formatted_messages = budget_manager.truncate_history(
                system_prompt=system_prompt,
                history=past_messages,
                current_user_message=payload.message
            )

            # Initialize LLM & Stream
            llm = LLMFactory.get_llm(provider=payload.provider, model=payload.model)
            async for token in llm.astream(formatted_messages):
                yield format_sse("token", {"token": token})
                accumulated_tokens.append(token)

        full_assistant_response = "".join(accumulated_tokens)

        # 5. DB Persistence of Assistant Response using a fresh connection/session inside generator
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db_stream:
            assistant_msg = await crud_session.add_message(
                db_stream,
                session_id=payload.session_id,
                role="assistant",
                content=full_assistant_response,
                citations=citations
            )

        # Stream Done Event with message ID
        yield format_sse("done", {"message_id": str(assistant_msg.id)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
