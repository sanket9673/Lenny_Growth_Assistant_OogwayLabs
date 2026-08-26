import re
from typing import AsyncGenerator, Dict, Any, Optional
from app.models.artifact import ArtifactType

class ArtifactStreamParser:
    """
    Stateful parser that monitors LLM token stream for structured artifact tags:
    <lenny_artifact key="id" type="html|markdown|svg" title="Title">content</lenny_artifact>
    """
    
    START_TAG_REGEX = re.compile(
        r'<lenny_artifact\s+key=["\'](?P<key>[^"\']+)["\']\s+type=["\'](?P<type>html|markdown|svg)["\']\s+title=["\'](?P<title>[^"\']+)["\']>',
        re.IGNORECASE
    )
    END_TAG = "</lenny_artifact>"

    def __init__(self, session_id: str, message_id: str):
        self.session_id = session_id
        self.message_id = message_id
        self.buffer = ""
        self.in_artifact = False
        self.current_key: Optional[str] = None
        self.current_type: Optional[ArtifactType] = None
        self.current_title: Optional[str] = None
        self.current_content = ""

    async def parse_chunk(self, chunk: str) -> AsyncGenerator[Dict[str, Any], None]:
        self.buffer += chunk

        while len(self.buffer) > 0:
            if not self.in_artifact:
                match = self.START_TAG_REGEX.search(self.buffer)
                if match:
                    start_pos, end_pos = match.span()
                    # Yield clean chat text before artifact tag
                    text_before = self.buffer[:start_pos]
                    if text_before:
                        yield {"type": "text", "content": text_before}
                    
                    self.current_key = match.group("key")
                    self.current_type = ArtifactType(match.group("type").lower())
                    self.current_title = match.group("title")
                    self.current_content = ""
                    self.in_artifact = True

                    yield {
                        "type": "sse",
                        "event": "artifact_start",
                        "data": {
                            "artifact_key": self.current_key,
                            "type": self.current_type.value,
                            "title": self.current_title,
                            "session_id": self.session_id,
                            "message_id": self.message_id
                        }
                    }

                    self.buffer = self.buffer[end_pos:]
                else:
                    # Retain potential partial start tag in buffer
                    cutoff = max(0, len(self.buffer) - 100)
                    yield_text = self.buffer[:cutoff]
                    self.buffer = self.buffer[cutoff:]
                    if yield_text:
                        yield {"type": "text", "content": yield_text}
                    break
            else:
                end_pos = self.buffer.find(self.END_TAG)
                if end_pos != -1:
                    content_chunk = self.buffer[:end_pos]
                    self.current_content += content_chunk
                    
                    if content_chunk:
                        yield {
                            "type": "sse",
                            "event": "artifact_chunk",
                            "data": {
                                "artifact_key": self.current_key,
                                "chunk": content_chunk
                            }
                        }

                    yield {
                        "type": "sse",
                        "event": "artifact_complete",
                        "data": {
                            "artifact_key": self.current_key,
                            "title": self.current_title,
                            "type": self.current_type.value,
                            "content": self.current_content,
                            "session_id": self.session_id,
                            "message_id": self.message_id
                        }
                    }

                    self.buffer = self.buffer[end_pos + len(self.END_TAG):]
                    self.in_artifact = False
                    self.current_key = None
                    self.current_type = None
                    self.current_title = None
                else:
                    # Flush stream chunk inside artifact
                    content_chunk = self.buffer
                    self.current_content += content_chunk
                    self.buffer = ""
                    if content_chunk:
                        yield {
                            "type": "sse",
                            "event": "artifact_chunk",
                            "data": {
                                "artifact_key": self.current_key,
                                "chunk": content_chunk
                            }
                        }
                    break

    async def finalize(self) -> AsyncGenerator[Dict[str, Any], None]:
        if self.buffer:
            if not self.in_artifact:
                yield {"type": "text", "content": self.buffer}
            else:
                # If stream ends with an incomplete block, yield the content chunk
                yield {
                    "type": "sse",
                    "event": "artifact_chunk",
                    "data": {
                        "artifact_key": self.current_key,
                        "chunk": self.buffer
                    }
                }
            self.buffer = ""
