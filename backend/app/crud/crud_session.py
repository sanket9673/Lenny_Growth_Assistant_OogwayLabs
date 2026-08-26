import uuid
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.models import Session, Message


async def create_session(db: AsyncSession, provider: str, model: str) -> Session:
    """Create and persist a new user chat session."""
    session = Session(
        id=uuid.uuid4(),
        provider=provider,
        model=model
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: UUID) -> Optional[Session]:
    """Retrieve a session by its UUID."""
    stmt = select(Session).where(Session.id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_session_messages(
    db: AsyncSession, session_id: UUID, limit: int = 20
) -> List[Message]:
    """Fetch recent messages for a given session sorted chronologically."""
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_message(
    db: AsyncSession,
    session_id: UUID,
    role: str,
    content: str,
    citations: Optional[List[Dict[str, Any]]] = None,
) -> Message:
    """Add a new message (user/assistant) with optional source citations to a session."""
    message = Message(
        id=uuid.uuid4(),
        session_id=session_id,
        role=role,
        content=content,
        citations=citations or [],
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message
