from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud.crud_artifact import crud_artifact
from app.schemas.artifact import ArtifactResponse

router = APIRouter()

@router.get("/sessions/{session_id}/artifacts", response_model=List[ArtifactResponse])
async def get_session_artifacts(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch the latest revision of all artifacts created in a chat session."""
    artifacts = await crud_artifact.list_session_artifacts(db, session_id)
    return artifacts

@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact_by_id(
    artifact_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch specific artifact revision details."""
    artifact = await crud_artifact.get_by_id(db, artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return artifact

@router.get("/sessions/{session_id}/artifacts/{artifact_key}/history", response_model=List[ArtifactResponse])
async def get_artifact_history(
    session_id: str,
    artifact_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch full version timeline for a named artifact."""
    history = await crud_artifact.get_version_history(db, session_id, artifact_key)
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No revision history found")
    return history
