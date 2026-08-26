from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schema import TranscriptChunk
from app.ingestion.chunker import ChunkPayload
from app.ingestion.embedder import EmbeddingEngine
from app.core.logging import logger

class VectorStoreManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedder = EmbeddingEngine()

    async def upsert_chunks(self, chunks: List[ChunkPayload], batch_size: int = 50) -> int:
        if not chunks:
            return 0

        inserted_count = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            contents = [c.content for c in batch]
            embeddings = self.embedder.embed_texts(contents)

            for chunk_payload, embedding in zip(batch, embeddings):
                # Check for existing chunk duplicate based on content hash or title+index
                stmt = select(TranscriptChunk).where(
                    (TranscriptChunk.transcript_title == chunk_payload.transcript_title) &
                    (TranscriptChunk.chunk_index == chunk_payload.chunk_index)
                )
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    existing.content = chunk_payload.content
                    existing.speaker = chunk_payload.speaker
                    existing.timestamp_start = chunk_payload.timestamp_start
                    existing.content_hash = chunk_payload.content_hash
                    existing.embedding = embedding
                    existing.publication_date = chunk_payload.publication_date
                else:
                    db_chunk = TranscriptChunk(
                        transcript_title=chunk_payload.transcript_title,
                        guest_name=chunk_payload.guest_name,
                        publication_date=chunk_payload.publication_date,
                        chunk_index=chunk_payload.chunk_index,
                        content=chunk_payload.content,
                        speaker=chunk_payload.speaker,
                        timestamp_start=chunk_payload.timestamp_start,
                        content_hash=chunk_payload.content_hash,
                        embedding=embedding
                    )
                    self.session.add(db_chunk)
                inserted_count += 1

            await self.session.flush()

        await self.session.commit()
        logger.info(f"Successfully processed and stored {inserted_count} chunks.")
        return inserted_count
