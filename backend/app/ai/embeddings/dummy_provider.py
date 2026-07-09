import random

from app.ai.embeddings.base import EmbeddingProvider


class DummyEmbeddingProvider(EmbeddingProvider):
    async def generate_embedding(
        self,
        text: str,
        dimension: int,
    ) -> list[float]:
        return [random.uniform(-0.01, 0.01) for _ in range(dimension)]