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


class SessionDetailResponse(BaseModel):
    id: UUID
    provider: str
    model: str
    messages: List[MessageSchema]

    class Config:
        from_attributes = True


@router.post("", response_model=SessionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    session = await crud_session.create_session(db, provider=payload.provider, model=payload.model)
    return SessionDetailResponse(
        id=session.id,
        provider=session.provider,
        model=session.model,
        messages=[]
    )


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
        provider=session.provider,
        model=session.model,
        messages=[MessageSchema.model_validate(m) for m in messages]
    )
