from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import TranscriptChunk
from app.rag.embeddings import EmbeddingEngine


@dataclass
class RetrievedChunk:
    chunk_id: str
    guest_name: str
    transcript_title: str
    timestamp_start: float
    speaker: str
    content: str
    distance: float

    def to_citation(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "guest_name": self.guest_name,
            "transcript_title": self.transcript_title,
            "timestamp_start": self.timestamp_start,
            "speaker": self.speaker,
        }


class TranscriptRetriever:
    def __init__(self, db: AsyncSession, embedding_engine: Optional[EmbeddingEngine] = None):
        self.db = db
        self.embedding_engine = embedding_engine or EmbeddingEngine()

    async def retrieve_relevant_chunks(
        self, query: str, top_k: int = 5, distance_threshold: float = 0.45
    ) -> Tuple[List[RetrievedChunk], bool]:
        """
        Embeds user query, executes vector cosine distance search against PostgreSQL pgvector,
        filters by distance threshold, and returns relevant chunks + context status flag.
        """
        query_vector = await self.embedding_engine.embed_query(query)
        
        # pgvector cosine distance: lower value means higher similarity
        distance_expr = TranscriptChunk.embedding.cosine_distance(query_vector)
        
        stmt = (
            select(TranscriptChunk, distance_expr.label("distance"))
            .order_by(distance_expr)
            .limit(top_k)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()

        retrieved_chunks: List[RetrievedChunk] = []
        for chunk, distance in rows:
            dist_val = float(distance)
            if dist_val <= distance_threshold:
                try:
                    ts_start = float(chunk.timestamp_start) if chunk.timestamp_start else 0.0
                except (ValueError, TypeError):
                    ts_start = 0.0
                retrieved_chunks.append(
                    RetrievedChunk(
                        chunk_id=str(chunk.id),
                        guest_name=chunk.guest_name,
                        transcript_title=chunk.transcript_title,
                        timestamp_start=ts_start,
                        speaker=chunk.speaker or "Unknown",
                        content=chunk.content,
                        distance=dist_val,
                    )
                )

        has_context = len(retrieved_chunks) > 0
        return retrieved_chunks, has_context
