from openai import AsyncOpenAI, OpenAIError

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.openai_error_handler import handle_openai_error
from app.core.config import settings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model_name = model_name

    async def generate_embedding(
        self,
        text: str,
        dimension: int,
    ) -> list[float]:
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=text,
            )
        except OpenAIError as exc:
            handle_openai_error(exc)

        vector = response.data[0].embedding

        if len(vector) != dimension:
            raise ValueError(
                f"Embedding dimension mismatch. expected={dimension}, actual={len(vector)}"
            )

        return vector
