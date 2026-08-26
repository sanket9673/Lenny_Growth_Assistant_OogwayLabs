from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/health")
async def check_health(db: AsyncSession = Depends(get_db)):
    # Check DB Connection
    await db.execute(text("SELECT 1"))
    
    # Check Vector Extension
    ext_result = await db.execute(
        text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    )
    has_vector = ext_result.scalar_one_or_none() is not None

    # Get Chunk Count
    count_result = await db.execute(text("SELECT COUNT(*) FROM transcript_chunks"))
    chunk_count = count_result.scalar_one()

    return {
        "status": "healthy",
        "database": "connected",
        "pgvector_ready": has_vector,
        "total_chunks_indexed": chunk_count
    }
