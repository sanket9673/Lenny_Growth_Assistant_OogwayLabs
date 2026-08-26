import json
import asyncio
import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
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

from app.agents.router import SkillRouter
from app.skills.ship30.pipeline import Ship30SkillEngine

router = APIRouter()
logger = logging.getLogger(__name__)


# ==========================================
# FEATURE 3: RAG SESSION SCHEMAS & ENDPOINT
# ==========================================

class ChatStreamRequest(BaseModel):
    session_id: UUID
    message: str
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"
    skill_preset: Optional[str] = None
    skillPreset: Optional[str] = None


def format_sse(event: str, data: dict) -> str:
    payload = {"type": event, **data}
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


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

    # Detect preset or route to skills
    skill_preset = payload.skill_preset or payload.skillPreset
    skill_router = SkillRouter(llm_factory=LLMFactory)
    route_decision = await skill_router.route(payload.message, skill_override=skill_preset)

    async def event_generator() -> AsyncGenerator[str, None]:
        # Stream Citations Event first. Force JSON payload type='citations' for the frontend
        yield format_sse("citation", {"citations": citations, "type": "citations"})

        accumulated_tokens = []
        
        # Generate assistant message ID early so parser/engine can reference it
        import uuid
        assistant_message_id = uuid.uuid4()

        if route_decision.selected_skill == "ship30":
            # Run Ship30 Skill Engine
            llm = LLMFactory.get_llm(provider=payload.provider, model=payload.model)
            engine = Ship30SkillEngine(llm_factory=llm)
            context_chunks_dict = [
                {
                    "guest_name": chunk.guest_name,
                    "episode": chunk.transcript_title,
                    "content": chunk.content
                }
                for chunk in retrieved_chunks
            ]
            
            async for event in engine.run_stream(payload.message, context_chunks_dict):
                if event["event"] == "skill_start":
                    yield format_sse("skill_progress", {
                        "skillName": "Ship 30 Essay",
                        "currentPhase": "Planning Outline",
                        "totalPhases": 3,
                        "phaseIndex": 1,
                        "details": "Initializing essay outline and structure..."
                    })
                elif event["event"] == "skill_progress":
                    phase_data = event["data"]
                    if phase_data.get("phase") == "drafting_sections":
                        yield format_sse("skill_progress", {
                            "skillName": "Ship 30 Essay",
                            "currentPhase": "Drafting Sections",
                            "totalPhases": 3,
                            "phaseIndex": 2,
                            "details": f"Drafting section {phase_data.get('current_section')} of {phase_data.get('total_sections')}..."
                        })
                    elif phase_data.get("phase") == "polishing_format":
                        yield format_sse("skill_progress", {
                            "skillName": "Ship 30 Essay",
                            "currentPhase": "Polishing Format",
                            "totalPhases": 3,
                            "phaseIndex": 3,
                            "details": "Applying 1-3-1 cadence and 4 A's hook..."
                        })
                elif event["event"] == "token":
                    token_text = event["data"]["text"]
                    yield format_sse("token", {"text": token_text})
                    accumulated_tokens.append(token_text)
                elif event["event"] == "done":
                    # Generate the essay markdown as the content
                    final_essay_content = "".join(accumulated_tokens)
                    
                    artifact_data = {
                        "artifact_key": "ship30-essay",
                        "title": "Ship 30 Product-Market Fit Essay",
                        "type": "markdown",
                        "content": final_essay_content,
                        "version": 1,
                        "session_id": str(payload.session_id),
                        "message_id": str(assistant_message_id)
                    }
                    yield format_sse("artifact", {"artifact": artifact_data})
                    
                    # Persist the artifact to the DB
                    from app.core.database import AsyncSessionLocal
                    from app.crud.crud_artifact import crud_artifact
                    from app.schemas.artifact import ArtifactCreate
                    from app.models.artifact import ArtifactType
                    async with AsyncSessionLocal() as db_stream:
                        await crud_artifact.create_or_version(
                            db_stream,
                            ArtifactCreate(
                                session_id=str(payload.session_id),
                                message_id=str(assistant_message_id),
                                artifact_key="ship30-essay",
                                title="Ship 30 Product-Market Fit Essay",
                                type=ArtifactType.MARKDOWN,
                                content=final_essay_content
                            )
                        )
        else:
            from app.artifacts.parser import ArtifactStreamParser
            parser = ArtifactStreamParser(session_id=str(payload.session_id), message_id=str(assistant_message_id))

            if not has_context:
                # Empty context fallback
                refusal_msg = REFUSAL_RESPONSE
                yield format_sse("token", {"text": refusal_msg})
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
                    async for item in parser.parse_chunk(token):
                        if item["type"] == "text":
                            yield format_sse("token", {"text": item["content"]})
                            accumulated_tokens.append(item["content"])
                        elif item["type"] == "sse":
                            # Stream real-time artifact chunks or completes
                            if item["event"] == "artifact_complete":
                                artifact_data = {
                                    "artifact_key": item["data"]["artifact_key"],
                                    "title": item["data"]["title"],
                                    "type": item["data"]["type"],
                                    "content": item["data"]["content"],
                                    "version": item["data"].get("version", 1),
                                    "session_id": str(payload.session_id),
                                    "message_id": str(assistant_message_id)
                                }
                                yield format_sse("artifact", {"artifact": artifact_data})
                                
                                from app.core.database import AsyncSessionLocal
                                from app.crud.crud_artifact import crud_artifact
                                from app.schemas.artifact import ArtifactCreate
                                from app.models.artifact import ArtifactType
                                async with AsyncSessionLocal() as db_stream:
                                    await crud_artifact.create_or_version(
                                        db_stream,
                                        ArtifactCreate(
                                            session_id=str(payload.session_id),
                                            message_id=str(assistant_message_id),
                                            artifact_key=item["data"]["artifact_key"],
                                            title=item["data"]["title"],
                                            type=ArtifactType(item["data"]["type"]),
                                            content=item["data"]["content"]
                                        )
                                    )

                async for item in parser.finalize():
                    if item["type"] == "text":
                        yield format_sse("token", {"text": item["content"]})
                        accumulated_tokens.append(item["content"])
                    elif item["type"] == "sse":
                        if item["event"] == "artifact_complete":
                            artifact_data = {
                                "artifact_key": item["data"]["artifact_key"],
                                "title": item["data"]["title"],
                                "type": item["data"]["type"],
                                "content": item["data"]["content"],
                                "version": item["data"].get("version", 1),
                                "session_id": str(payload.session_id),
                                "message_id": str(assistant_message_id)
                            }
                            yield format_sse("artifact", {"artifact": artifact_data})
                            
                            from app.core.database import AsyncSessionLocal
                            from app.crud.crud_artifact import crud_artifact
                            from app.schemas.artifact import ArtifactCreate
                            from app.models.artifact import ArtifactType
                            async with AsyncSessionLocal() as db_stream:
                                await crud_artifact.create_or_version(
                                    db_stream,
                                    ArtifactCreate(
                                        session_id=str(payload.session_id),
                                        message_id=str(assistant_message_id),
                                        artifact_key=item["data"]["artifact_key"],
                                        title=item["data"]["title"],
                                        type=ArtifactType(item["data"]["type"]),
                                        content=item["data"]["content"]
                                    )
                                )

        full_assistant_response = "".join(accumulated_tokens)

        # 5. DB Persistence of Assistant Response using a fresh connection/session inside generator
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db_stream:
            from app.db.models import Message
            assistant_msg = Message(
                id=assistant_message_id,
                session_id=payload.session_id,
                role="assistant",
                content=full_assistant_response,
                citations=citations
            )
            db_stream.add(assistant_msg)
            await db_stream.commit()

        # Stream Done Event with message ID for old tests, and literal DONE for new frontend
        yield format_sse("done", {"message_id": str(assistant_message_id)})
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==========================================
# FEATURE 4: SHIP 30 CONTENT ENGINE SCHEMAS & ENDPOINT
# ==========================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    skill_override: Optional[str] = None
    chat_history: Optional[List[ChatMessage]] = []


# Dummy LLM Factory & Retriever dependencies for engine execution context
class DummyLLMFactory:
    async def generate(self, system_prompt: str, prompt: str, temperature: float = 0.3, response_format: str = "text") -> str:
        if response_format == "json":
            if "selected_skill" in prompt:
                return json.dumps({"selected_skill": "ship30", "confidence": 0.95, "reasoning": "Essay requested"})
            return json.dumps({
                "topic": "Growth Leadership",
                "target_audience": "Growth PMs",
                "core_thesis": "Execution drives retention.",
                "hook_attention": "Retention is the ultimate metric for growth.",
                "hook_agitate": "Most teams optimize top of funnel and bleed users.",
                "hook_articulate": "The problem is lack of activation loops.",
                "hook_action": "Build systematic activation cadences.",
                "sections": [
                    {"section_index": i, "title": f"Section {i}: Strategy Framework", "key_takeaway": "Drive retention", "transcript_citations": ["Lenny Rachitsky"], "target_word_count": 300}
                    for i in range(1, 5)
                ],
                "total_target_words": 1250
            })
        
        return (
            "Building high-performing growth teams requires relentless prioritization and rigorous execution. "
            "According to [Lenny Rachitsky, Episode 42], product market fit must precede any acquisition spend. "
            "First, focus on retention curves. If your retention curve does not flatten, no acquisition budget will save you. "
            "Second, establish clear activation milestones. Ensure users experience the core value within their first session.\n\n"
            "Execution requires continuous alignment across design, engineering, and data science. "
            "Create weekly growth reviews. Measure output metrics against input leverage points.\n\n"
            "**Key Takeaway: Retention compounds acquisition efficiency over time.**"
        )


class DummyRetriever:
    async def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        return [
            {
                "guest_name": "Elena Verna",
                "episode": "Product-Led Growth & B2B Retention",
                "content": "PLG requires virality and self-serve onboarding. Retention is compounding."
            },
            {
                "guest_name": "Casey Winters",
                "episode": "Scaling Retention Loops",
                "content": "SEO and Referral loops are the primary growth engines that sustain long-term scale."
            }
        ]


def get_llm_factory():
    return DummyLLMFactory()


def get_retriever():
    return DummyRetriever()


@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    llm_factory: Any = Depends(get_llm_factory),
    retriever: Any = Depends(get_retriever)
):
    """
    Streaming SSE endpoint integrating intent routing and Ship30 multi-pass generation.
    """
    skill_router = SkillRouter(llm_factory=llm_factory)
    route_decision = await skill_router.route(request.message, skill_override=request.skill_override)

    async def event_generator():
        try:
            context_chunks = await retriever.retrieve(request.message)

            if route_decision.selected_skill == "ship30":
                engine = Ship30SkillEngine(llm_factory=llm_factory)
                async for event in engine.run_stream(request.message, context_chunks):
                    yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
            else:
                yield f"event: skill_start\ndata: {json.dumps({'skill': 'standard_qa'})}\n\n"
                answer = await llm_factory.generate(
                    system_prompt="You are Lenny's Growth Assistant.",
                    prompt=request.message
                )
                yield f"event: token\ndata: {json.dumps({'text': answer})}\n\n"
                yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
