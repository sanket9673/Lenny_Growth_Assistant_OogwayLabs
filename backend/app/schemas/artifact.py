from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.artifact import ArtifactType

class ArtifactBase(BaseModel):
    artifact_key: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    type: ArtifactType
    content: str

class ArtifactCreate(ArtifactBase):
    session_id: str
    message_id: str

class ArtifactResponse(ArtifactBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    message_id: str
    version: int
    created_at: datetime
    updated_at: datetime

class ArtifactStreamEvent(BaseModel):
    event: str  # "artifact_start" | "artifact_chunk" | "artifact_complete"
    artifact_id: Optional[str] = None
    artifact_key: str
    title: str
    type: ArtifactType
    chunk: Optional[str] = None
    version: int = 1
    session_id: str
