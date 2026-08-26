import hashlib
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from app.ingestion.parser import ParsedTranscript

class ChunkPayload(BaseModel):
    transcript_title: str
    guest_name: str
    publication_date: Optional[date]
    chunk_index: int
    content: str
    speaker: Optional[str]
    timestamp_start: Optional[str]
    content_hash: str

class SemanticChunker:
    def __init__(self, target_words: int = 400, overlap_words: int = 50):
        self.target_words = target_words
        self.overlap_words = overlap_words

    def _compute_hash(self, text: str, title: str, index: int) -> str:
        key = f"{title}_{index}_{text}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def chunk_transcript(self, transcript: ParsedTranscript) -> List[ChunkPayload]:
        chunks: List[ChunkPayload] = []
        chunk_index = 0

        # Build combined blocks from turns
        blocks = []
        for turn in transcript.turns:
            prefix = ""
            if turn.speaker:
                prefix += f"{turn.speaker}: "
            blocks.append({
                "speaker": turn.speaker,
                "timestamp": turn.timestamp,
                "text": prefix + turn.text
            })

        if not blocks:
            # Fallback for empty/unparsed turn structures
            words = transcript.raw_body.split()
            for i in range(0, len(words), self.target_words - self.overlap_words):
                chunk_words = words[i:i + self.target_words]
                chunk_text = " ".join(chunk_words)
                formatted_content = f"Episode: {transcript.title} | Guest: {transcript.guest_name}\n\n{chunk_text}"
                chash = self._compute_hash(formatted_content, transcript.title, chunk_index)
                chunks.append(ChunkPayload(
                    transcript_title=transcript.title,
                    guest_name=transcript.guest_name,
                    publication_date=transcript.publication_date,
                    chunk_index=chunk_index,
                    content=formatted_content,
                    speaker=None,
                    timestamp_start=None,
                    content_hash=chash
                ))
                chunk_index += 1
            return chunks

        current_block_texts: List[str] = []
        current_word_count = 0
        current_speaker: Optional[str] = blocks[0]["speaker"]
        current_timestamp: Optional[str] = blocks[0]["timestamp"]

        for block in blocks:
            block_words = block["text"].split()
            
            if current_word_count + len(block_words) > self.target_words and current_block_texts:
                # Flush chunk
                raw_chunk_text = "\n".join(current_block_texts)
                contextual_text = f"Context - Episode: {transcript.title} | Guest: {transcript.guest_name}\n\n{raw_chunk_text}"
                chash = self._compute_hash(contextual_text, transcript.title, chunk_index)
                
                chunks.append(ChunkPayload(
                    transcript_title=transcript.title,
                    guest_name=transcript.guest_name,
                    publication_date=transcript.publication_date,
                    chunk_index=chunk_index,
                    content=contextual_text,
                    speaker=current_speaker,
                    timestamp_start=current_timestamp,
                    content_hash=chash
                ))
                chunk_index += 1

                # Carry over overlap
                overlap_text = " ".join(raw_chunk_text.split()[-self.overlap_words:])
                current_block_texts = [overlap_text, block["text"]]
                current_word_count = len(overlap_text.split()) + len(block_words)
                current_speaker = block["speaker"]
                current_timestamp = block["timestamp"]
            else:
                current_block_texts.append(block["text"])
                current_word_count += len(block_words)

        if current_block_texts:
            raw_chunk_text = "\n".join(current_block_texts)
            contextual_text = f"Context - Episode: {transcript.title} | Guest: {transcript.guest_name}\n\n{raw_chunk_text}"
            chash = self._compute_hash(contextual_text, transcript.title, chunk_index)
            chunks.append(ChunkPayload(
                transcript_title=transcript.title,
                guest_name=transcript.guest_name,
                publication_date=transcript.publication_date,
                chunk_index=chunk_index,
                content=contextual_text,
                speaker=current_speaker,
                timestamp_start=current_timestamp,
                content_hash=chash
            ))

        return chunks
