from typing import List
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schema import TranscriptChunk
from app.ingestion.chunker import ChunkPayload
from app.ingestion.embedder import EmbeddingEngine
from app.core.logging import logger

class VectorStoreManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedder = EmbeddingEngine()

    async def upsert_chunks(self, chunks: List[ChunkPayload], batch_size: int = 100) -> int:
        if not chunks:
            return 0

        inserted_count = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            contents = [c.content for c in batch]
            embeddings = self.embedder.embed_texts(contents)

            values_to_insert = []
            for chunk_payload, embedding in zip(batch, embeddings):
                values_to_insert.append({
                    "transcript_title": chunk_payload.transcript_title,
                    "guest_name": chunk_payload.guest_name,
                    "publication_date": chunk_payload.publication_date,
                    "chunk_index": chunk_payload.chunk_index,
                    "content": chunk_payload.content,
                    "speaker": chunk_payload.speaker,
                    "timestamp_start": chunk_payload.timestamp_start,
                    "content_hash": chunk_payload.content_hash,
                    "embedding": embedding
                })

            stmt = insert(TranscriptChunk).values(values_to_insert)
            # Perform atomic bulk upsert using PostgreSQL ON CONFLICT clause
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["transcript_title", "chunk_index"],
                set_={
                    "content": stmt.excluded.content,
                    "guest_name": stmt.excluded.guest_name,
                    "publication_date": stmt.excluded.publication_date,
                    "speaker": stmt.excluded.speaker,
                    "timestamp_start": stmt.excluded.timestamp_start,
                    "content_hash": stmt.excluded.content_hash,
                    "embedding": stmt.excluded.embedding,
                }
            )
            await self.session.execute(upsert_stmt)
            inserted_count += len(batch)

        await self.session.commit()
        logger.info(f"Successfully batch-upserted {inserted_count} chunks.")
        return inserted_count
