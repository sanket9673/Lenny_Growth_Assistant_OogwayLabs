import pytest
import uuid
# Import all database models to register them in Base.metadata for foreign keys
from app.models.schema import Session, Message, TranscriptChunk
from app.artifacts.parser import ArtifactStreamParser
from app.models.artifact import ArtifactType, Artifact
from app.schemas.artifact import ArtifactCreate
from app.crud.crud_artifact import crud_artifact

@pytest.mark.asyncio
async def test_parser_single_chunk():
    parser = ArtifactStreamParser(session_id="sess_1", message_id="msg_1")
    stream_input = '<lenny_artifact key="chart_1" type="html" title="Growth Chart font"><h1>Growth</h1></lenny_artifact>'
    
    events = []
    async for event in parser.parse_chunk(stream_input):
        events.append(event)
    
    assert len(events) >= 2
    assert events[0]["event"] == "artifact_start"
    assert events[0]["data"]["artifact_key"] == "chart_1"
    assert events[-1]["event"] == "artifact_complete"
    assert events[-1]["data"]["content"] == "<h1>Growth</h1>"

@pytest.mark.asyncio
async def test_artifact_crud_versioning(db_session):
    # Enforce foreign key constraints by creating parent session and messages first
    sess_id = uuid.uuid4()
    msg_id_1 = uuid.uuid4()
    msg_id_2 = uuid.uuid4()
    
    session_row = Session(id=sess_id, provider="anthropic", model="claude-3-5-sonnet")
    db_session.add(session_row)
    
    msg_row_1 = Message(id=msg_id_1, session_id=sess_id, role="user", content="Initial prompt")
    msg_row_2 = Message(id=msg_id_2, session_id=sess_id, role="assistant", content="Assistant response")
    db_session.add(msg_row_1)
    db_session.add(msg_row_2)
    
    await db_session.commit()

    artifact_v1 = ArtifactCreate(
        session_id=str(sess_id),
        message_id=str(msg_id_1),
        artifact_key="funnel_doc",
        title="Funnel Strategy",
        type=ArtifactType.MARKDOWN,
        content="# Funnel Overview v1"
    )
    res_v1 = await crud_artifact.create_or_version(db_session, artifact_v1)
    assert res_v1.version == 1
    assert res_v1.content == "# Funnel Overview v1"

    artifact_v2 = ArtifactCreate(
        session_id=str(sess_id),
        message_id=str(msg_id_2),
        artifact_key="funnel_doc",
        title="Funnel Strategy",
        type=ArtifactType.MARKDOWN,
        content="# Funnel Overview v2"
    )
    res_v2 = await crud_artifact.create_or_version(db_session, artifact_v2)
    assert res_v2.version == 2
    assert res_v2.content == "# Funnel Overview v2"

    history = await crud_artifact.get_version_history(db_session, str(sess_id), "funnel_doc")
    assert len(history) == 2
