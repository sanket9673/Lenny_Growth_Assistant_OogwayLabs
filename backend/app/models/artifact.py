import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ArtifactType(str, Enum):
    HTML = "html"
    MARKDOWN = "markdown"
    SVG = "svg"

class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_key: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Unique identifier per session for tracking revisions"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ArtifactType] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    session: Mapped["Session"] = relationship("Session", back_populates="artifacts")
    message: Mapped["Message"] = relationship("Message", back_populates="artifacts")

    __table_args__ = (
        UniqueConstraint("session_id", "artifact_key", "version", name="uq_session_artifact_version"),
        Index("ix_artifacts_session_key", "session_id", "artifact_key"),
    )
