from typing import List
from fastembed import TextEmbedding
from app.core.config import settings
from app.core.logging import logger

class EmbeddingEngine:
    _instance: "EmbeddingEngine" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
            logger.info(f"Initializing FastEmbed model: {settings.EMBEDDING_MODEL_NAME}")
            cls._instance.model = TextEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)
        return cls._instance

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings_generator = self.model.embed(texts)
        return [embedding.tolist() for embedding in embeddings_generator]

    def embed_text(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]
