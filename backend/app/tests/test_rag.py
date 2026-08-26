import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.rag.retriever import TranscriptRetriever, RetrievedChunk
from app.rag.prompt import build_grounded_system_prompt, REFUSAL_RESPONSE
from app.crud import crud_session


@pytest.mark.asyncio
async def test_retriever_vector_similarity():
    """Verify that chunks exceeding distance_threshold are filtered out."""
    mock_db = MagicMock()
    mock_execute_result = MagicMock()
    
    # Mocking TranscriptChunk records from DB
    mock_chunk_valid = MagicMock()
    mock_chunk_valid.id = uuid.uuid4()
    mock_chunk_valid.guest_name = "Shreyas Doshi"
    mock_chunk_valid.transcript_title = "Product Sense"
    mock_chunk_valid.timestamp_start = "120.0"
    mock_chunk_valid.speaker = "Shreyas Doshi"
    mock_chunk_valid.content = "LNO framework prioritizes tasks."

    mock_chunk_invalid = MagicMock()
    mock_chunk_invalid.id = uuid.uuid4()
    mock_chunk_invalid.guest_name = "Random Guest"
    mock_chunk_invalid.transcript_title = "Irrelevant Topic"
    mock_chunk_invalid.timestamp_start = "10.0"
    mock_chunk_invalid.speaker = "Random"
    mock_chunk_invalid.content = "Unrelated contents."

    # Return valid chunk with distance 0.3 (pass) and invalid with 0.8 (fail)
    mock_execute_result.all.return_value = [
        (mock_chunk_valid, 0.30),
        (mock_chunk_invalid, 0.80),
    ]
    mock_db.execute = AsyncMock(return_value=mock_execute_result)

    with patch("app.rag.embeddings.EmbeddingEngine.embed_query", return_value=[0.1] * 1536):
        retriever = TranscriptRetriever(mock_db)
        chunks, has_context = await retriever.retrieve_relevant_chunks("Explain LNO framework", top_k=5, distance_threshold=0.45)

        assert has_context is True
        assert len(chunks) == 1
        assert chunks[0].guest_name == "Shreyas Doshi"
        assert chunks[0].distance == 0.30



@pytest.mark.asyncio
async def test_grounding_refusal():
    """Verify system prompt refusal logic when context is empty."""
    system_prompt = build_grounded_system_prompt([])
    assert "[CONTEXT AVAILABILITY]: NONE" in system_prompt
    assert REFUSAL_RESPONSE in system_prompt


@pytest.mark.asyncio
async def test_session_multi_turn_persistence(db_session):
    """Simulate creating a session and appending multi-turn messages."""
    session = await crud_session.create_session(db_session, provider="anthropic", model="claude-3-5-sonnet-20241022")
    assert session.id is not None

    msg1 = await crud_session.add_message(db_session, session.id, role="user", content="What is PLG?")
    msg2 = await crud_session.add_message(db_session, session.id, role="assistant", content="Product Led Growth...", citations=[])

    history = await crud_session.get_session_messages(db_session, session.id)
    assert len(history) == 2
    assert history[0].content == "What is PLG?"
    assert history[1].content == "Product Led Growth..."


@pytest.mark.asyncio
async def test_sse_chat_stream(client: AsyncClient, db_session):
    """Test full SSE streaming endpoint response structure."""
    session = await crud_session.create_session(db_session, provider="anthropic", model="claude-3-5-sonnet-20241022")

    with patch("app.rag.retriever.TranscriptRetriever.retrieve_relevant_chunks") as mock_retrieve, \
         patch("app.rag.llm_factory.LLMFactory.get_llm") as mock_llm_factory:

        # Mock retriever returning 1 chunk
        mock_retrieve.return_value = (
            [
                RetrievedChunk(
                    chunk_id="c123",
                    guest_name="Elena Verna",
                    transcript_title="B2B Growth",
                    timestamp_start=45.0,
                    speaker="Elena Verna",
                    content="Product led growth drives acquisition.",
                    distance=0.2,
                )
            ],
            True,
        )

        # Mock LLM stream generator
        mock_llm = MagicMock()
        async def mock_astream(messages):
            yield "Product "
            yield "Led "
            yield "Growth."
        mock_llm.astream = mock_astream
        mock_llm_factory.return_value = mock_llm

        response = await client.post(
            "/api/v1/chat/stream",
            json={
                "session_id": str(session.id),
                "message": "How does B2B PLG work?",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
            },
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        
        body = response.text
        assert "event: citation" in body
        assert "Elena Verna" in body
        assert "event: token" in body
        assert "event: done" in body
