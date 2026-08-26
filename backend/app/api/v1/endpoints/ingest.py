from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from app.ingestion.cli import run_ingestion

router = APIRouter()

class IngestionResponse(BaseModel):
    message: str
    status: str

@router.post("/ingest", response_model=IngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingestion(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(run_ingestion)
        return IngestionResponse(
            message="Transcript ingestion pipeline triggered in background.",
            status="queued"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger ingestion: {str(e)}"
        )
