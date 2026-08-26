from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud import crud_session

router = APIRouter()


class CreateSessionRequest(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"


class MessageSchema(BaseModel):
    id: UUID
    role: str
    content: str
    citations: List[dict] = []

    class Config:
        from_attributes = True


from datetime import datetime
from pydantic import Field, ConfigDict

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str = Field(default="New Session")
    createdAt: datetime = Field(validation_alias="created_at", serialization_alias="createdAt")
    updatedAt: datetime = Field(validation_alias="updated_at", serialization_alias="updatedAt")


class SessionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str = Field(default="New Session")
    provider: str
    model: str
    messages: List[MessageSchema]


class UpdateSessionTitleRequest(BaseModel):
    title: str


@router.post("", response_model=SessionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    session = await crud_session.create_session(db, provider=payload.provider, model=payload.model)
    return SessionDetailResponse(
        id=session.id,
        title=session.title or "New Session",
        provider=session.provider,
        model=session.model,
        messages=[]
    )


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db)
):
    sessions = await crud_session.list_sessions(db)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    session = await crud_session.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await crud_session.get_session_messages(db, session_id)
    return SessionDetailResponse(
        id=session.id,
        title=session.title or "New Session",
        provider=session.provider,
        model=session.model,
        messages=[MessageSchema.model_validate(m) for m in messages]
    )


@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    success = await crud_session.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "message": "Session deleted"}


@router.patch("/{session_id}", response_model=SessionResponse)
async def patch_session_title(
    session_id: UUID,
    payload: UpdateSessionTitleRequest,
    db: AsyncSession = Depends(get_db)
):
    session = await crud_session.update_session_title(db, session_id, payload.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.model_validate(session)
