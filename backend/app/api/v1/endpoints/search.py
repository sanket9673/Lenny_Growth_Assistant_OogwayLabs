from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.ingestion.embedder import EmbeddingEngine

router = APIRouter()

class SearchResultItem(BaseModel):
    transcript_title: str
    guest_name: str
    chunk_index: int
    speaker: Optional[str]
    timestamp_start: Optional[str]
    content: str
    similarity: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]

@router.get("/search", response_model=SearchResponse)
async def search_vector_store(
    query: str = Query(..., min_length=2, description="Semantic search query"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    try:
        embedder = EmbeddingEngine()
        query_vector = embedder.embed_text(query)

        # HNSW Cosine Distance search query using pgvector operator <=>
        stmt = text("""
            SELECT transcript_title, guest_name, chunk_index, speaker, timestamp_start, content,
                   1 - (embedding <=> :vector) as similarity
            FROM transcript_chunks
            ORDER BY embedding <=> :vector
            LIMIT :limit;
        """)

        res = await db.execute(stmt, {"vector": str(query_vector), "limit": limit})
        rows = res.fetchall()

        results = [
            SearchResultItem(
                transcript_title=row.transcript_title,
                guest_name=row.guest_name,
                chunk_index=row.chunk_index,
                speaker=row.speaker,
                timestamp_start=row.timestamp_start,
                content=row.content,
                similarity=round(float(row.similarity), 4)
            )
            for row in rows
        ]

        return SearchResponse(query=query, results=results)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing vector search: {str(e)}"
        )
