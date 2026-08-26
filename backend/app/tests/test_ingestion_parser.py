from pathlib import Path
import tempfile
from app.ingestion.parser import TranscriptParser

SAMPLE_TRANSCRIPT = """---
guest: "Brian Chesky"
title: "Designing Airbnb's Future"
publish_date: "2023-11-01"
---

Lenny (00:00): Welcome to the show.

Brian Chesky (00:05): Thanks for having me. Design is core to everything we build at Airbnb.
"""

def test_transcript_parser():
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as tf:
        tf.write(SAMPLE_TRANSCRIPT)
        tf_path = Path(tf.name)

    parsed = TranscriptParser.parse_file(tf_path)
    assert parsed.guest_name == "Brian Chesky"
    assert parsed.title == "Designing Airbnb's Future"
    assert len(parsed.turns) == 2
    assert parsed.turns[0].speaker == "Lenny"
    assert parsed.turns[1].speaker == "Brian Chesky"
    tf_path.unlink()
