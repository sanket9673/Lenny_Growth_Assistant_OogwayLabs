import re
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import frontmatter

class ParsedTurn:
    def __init__(self, speaker: Optional[str], timestamp: Optional[str], text: str):
        self.speaker = speaker
        self.timestamp = timestamp
        self.text = text

    def __repr__(self) -> str:
        return f"ParsedTurn(speaker='{self.speaker}', timestamp='{self.timestamp}', text='{self.text[:30]}...')"

class ParsedTranscript:
    def __init__(self, metadata: Dict[str, Any], turns: List[ParsedTurn], raw_body: str):
        self.guest_name: str = str(metadata.get("guest", metadata.get("guest_name", "Unknown Guest")))
        self.title: str = str(metadata.get("title", metadata.get("episode_title", "Untitled Episode")))
        
        raw_date = metadata.get("publish_date", metadata.get("date", None))
        self.publication_date: Optional[datetime.date] = None
        if raw_date:
            if isinstance(raw_date, datetime.date):
                self.publication_date = raw_date
            elif isinstance(raw_date, datetime.datetime):
                self.publication_date = raw_date.date()
            elif isinstance(raw_date, str):
                try:
                    self.publication_date = datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()
                except ValueError:
                    self.publication_date = None

        self.metadata = metadata
        self.turns = turns
        self.raw_body = raw_body

class TranscriptParser:
    # Pattern to match: [00:12:34] Speaker Name: Text or Speaker Name (00:12): Text
    TIMESTAMP_SPEAKER_PATTERN = re.compile(
        r"^(?:\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*)?(?:([^:\n]+):\s*)?(.*)$"
    )

    @classmethod
    def parse_file(cls, file_path: Path) -> ParsedTranscript:
        post = frontmatter.load(file_path)
        metadata = dict(post.metadata)
        body = post.content

        lines = body.split("\n")
        turns: List[ParsedTurn] = []
        current_speaker: Optional[str] = None
        current_timestamp: Optional[str] = None
        current_text_lines: List[str] = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check for header format like: **Lenny (01:23)**: or Lenny:
            match = re.match(r"^(?:\*\*)?([^:\(\n]+?)(?:\s*\(([^)\n]+)\))?(?:\*\*)?:\s*(.*)$", line_str)
            if match and len(match.group(1).strip()) < 50:
                if current_text_lines:
                    turns.append(ParsedTurn(
                        speaker=current_speaker,
                        timestamp=current_timestamp,
                        text=" ".join(current_text_lines)
                    ))
                    current_text_lines = []
                
                current_speaker = match.group(1).strip().replace("*", "")
                current_timestamp = match.group(2).strip() if match.group(2) else None
                remaining_text = match.group(3).strip()
                if remaining_text:
                    current_text_lines.append(remaining_text)
            else:
                current_text_lines.append(line_str)

        if current_text_lines:
            turns.append(ParsedTurn(
                speaker=current_speaker,
                timestamp=current_timestamp,
                text=" ".join(current_text_lines)
            ))

        return ParsedTranscript(metadata=metadata, turns=turns, raw_body=body)
