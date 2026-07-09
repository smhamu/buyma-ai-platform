from openai import AsyncOpenAI

from app.ai.embeddings.base import EmbeddingProvider
from app.core.config import settings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model_name = model_name

    async def generate_embedding(
        self,
        text: str,
        dimension: int,
    ) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.model_name,
            input=text,
        )

        vector = response.data[0].embedding

        if len(vector) != dimension:
            raise ValueError(
                f"Embedding dimension mismatch. expected={dimension}, actual={len(vector)}"
            )

        return vector