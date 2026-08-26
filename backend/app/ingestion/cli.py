import asyncio
from pathlib import Path
from app.core.database import AsyncSessionLocal, init_db
from app.ingestion.parser import TranscriptParser
from app.ingestion.chunker import SemanticChunker
from app.ingestion.vector_store import VectorStoreManager
from app.core.logging import logger

async def run_ingestion(data_dir: str = "./data/transcripts"):
    logger.info("Starting batch transcript ingestion...")
    await init_db()

    transcripts_path = Path(data_dir)
    if not transcripts_path.exists():
        # Try parent directory relative path (e.g. if run from backend/)
        alternative_path = Path("..") / data_dir
        if alternative_path.exists():
            transcripts_path = alternative_path
        else:
            # Try if run from backend/ but path was default ./data/transcripts
            alternative_path = Path("../data/transcripts")
            if alternative_path.exists():
                transcripts_path = alternative_path
            else:
                logger.error(f"Directory {data_dir} does not exist.")
                return

    files = list(transcripts_path.glob("*.md")) + list(transcripts_path.glob("*.txt"))
    logger.info(f"Found {len(files)} files for ingestion.")

    chunker = SemanticChunker()
    total_chunks = 0

    async with AsyncSessionLocal() as session:
        vector_store = VectorStoreManager(session)
        for idx, file_path in enumerate(files, 1):
            logger.info(f"[{idx}/{len(files)}] Parsing {file_path.name}...")
            parsed = TranscriptParser.parse_file(file_path)
            chunks = chunker.chunk_transcript(parsed)
            count = await vector_store.upsert_chunks(chunks)
            total_chunks += count
            logger.info(f"Ingested {count} chunks from {file_path.name}")

    logger.info(f"Ingestion process completed. Total chunks stored: {total_chunks}")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
