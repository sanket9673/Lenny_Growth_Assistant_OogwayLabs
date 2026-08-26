from typing import List
from app.ingestion.embedder import EmbeddingEngine as FastEmbedEngine

class EmbeddingEngine:
    """Wrapper around FastEmbed-based EmbeddingEngine exposing an async embed_query method."""
    def __init__(self):
        self.engine = FastEmbedEngine()

    async def embed_query(self, query: str) -> List[float]:
        return self.engine.embed_text(query)
