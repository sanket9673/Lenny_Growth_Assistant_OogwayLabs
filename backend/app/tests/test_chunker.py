from app.ingestion.parser import ParsedTranscript, ParsedTurn
from app.ingestion.chunker import SemanticChunker

def test_semantic_chunker():
    turns = [
        ParsedTurn(speaker="Lenny", timestamp="00:00", text="How do you define product velocity?"),
        ParsedTurn(speaker="Guest", timestamp="00:15", text="Velocity is direction plus speed. " * 50)
    ]
    parsed = ParsedTranscript(
        metadata={"guest": "Shreyas Doshi", "title": "Product Leadership"},
        turns=turns,
        raw_body=""
    )

    chunker = SemanticChunker(target_words=50, overlap_words=10)
    chunks = chunker.chunk_transcript(parsed)

    assert len(chunks) > 0
    assert "Shreyas Doshi" in chunks[0].content
    assert chunks[0].transcript_title == "Product Leadership"
