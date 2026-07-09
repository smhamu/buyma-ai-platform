from app.ai.embeddings.base import EmbeddingProvider
from app.ai.embeddings.dummy_provider import DummyEmbeddingProvider
from app.ai.embeddings.openai_provider import OpenAIEmbeddingProvider


class EmbeddingProviderFactory:
    @staticmethod
    def create(
        provider_code: str,
        model_name: str | None = None,
    ) -> EmbeddingProvider:
        if provider_code == "dummy":
            return DummyEmbeddingProvider()

        if provider_code == "openai":
            if model_name is None:
                raise ValueError("model_name is required for OpenAI provider")

            return OpenAIEmbeddingProvider(model_name=model_name)

        return DummyEmbeddingProvider()