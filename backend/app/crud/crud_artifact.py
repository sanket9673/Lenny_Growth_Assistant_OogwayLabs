import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.artifact import Artifact
from app.schemas.artifact import ArtifactCreate

class CRUDArtifact:
    async def get_by_id(self, db: AsyncSession, artifact_id: str) -> Optional[Artifact]:
        art_id = uuid.UUID(artifact_id) if isinstance(artifact_id, str) else artifact_id
        result = await db.execute(select(Artifact).where(Artifact.id == art_id))
        return result.scalars().first()

    async def get_latest_version(self, db: AsyncSession, session_id: str, artifact_key: str) -> Optional[Artifact]:
        sess_id = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
        query = (
            select(Artifact)
            .where(Artifact.session_id == sess_id, Artifact.artifact_key == artifact_key)
            .order_by(Artifact.version.desc())
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_version_history(self, db: AsyncSession, session_id: str, artifact_key: str) -> List[Artifact]:
        sess_id = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
        query = (
            select(Artifact)
            .where(Artifact.session_id == sess_id, Artifact.artifact_key == artifact_key)
            .order_by(Artifact.version.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def list_session_artifacts(self, db: AsyncSession, session_id: str) -> List[Artifact]:
        sess_id = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
        # Subquery to pick maximum version for each artifact_key in session
        subq = (
            select(Artifact.artifact_key, func.max(Artifact.version).label("max_ver"))
            .where(Artifact.session_id == sess_id)
            .group_by(Artifact.artifact_key)
            .subquery()
        )
        query = (
            select(Artifact)
            .join(
                subq,
                (Artifact.artifact_key == subq.c.artifact_key) & (Artifact.version == subq.c.max_ver)
            )
            .where(Artifact.session_id == sess_id)
            .order_by(Artifact.updated_at.desc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_or_version(self, db: AsyncSession, obj_in: ArtifactCreate) -> Artifact:
        sess_id = uuid.UUID(obj_in.session_id) if isinstance(obj_in.session_id, str) else obj_in.session_id
        msg_id = uuid.UUID(obj_in.message_id) if isinstance(obj_in.message_id, str) else obj_in.message_id

        latest = await self.get_latest_version(db, str(sess_id), obj_in.artifact_key)
        next_version = (latest.version + 1) if latest else 1

        db_obj = Artifact(
            id=uuid.uuid4(),
            session_id=sess_id,
            message_id=msg_id,
            artifact_key=obj_in.artifact_key,
            title=obj_in.title,
            type=obj_in.type,
            content=obj_in.content,
            version=next_version,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

crud_artifact = CRUDArtifact()
