import pytest
from sqlalchemy import text
from app.ingestion.chunker import ChunkPayload
from app.ingestion.vector_store import VectorStoreManager

@pytest.mark.asyncio
async def test_vector_upsert_and_similarity(test_db_session):
    manager = VectorStoreManager(test_db_session)
    
    payload = ChunkPayload(
        transcript_title="Test Episode",
        guest_name="Test Guest",
        publication_date=None,
        chunk_index=0,
        content="Product market fit requires extreme focus on customer feedback.",
        speaker="Test Guest",
        timestamp_start="01:00",
        content_hash="hash123"
    )

    count = await manager.upsert_chunks([payload])
    assert count == 1

    # Execute Cosine Distance Search
    query_vector = manager.embedder.embed_text("customer feedback product fit")
    stmt = text("""
        SELECT content, 1 - (embedding <=> :vector) as similarity
        FROM transcript_chunks
        ORDER BY embedding <=> :vector
        LIMIT 1;
    """)
    res = await test_db_session.execute(stmt, {"vector": str(query_vector)})
    row = res.fetchone()
    
    assert row is not None
    assert row[1] > 0.3
