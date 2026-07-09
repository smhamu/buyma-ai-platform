from app.ai.embeddings.base import EmbeddingProvider
from app.ai.embeddings.dummy_provider import DummyEmbeddingProvider


class EmbeddingProviderFactory:
    @staticmethod
    def create(provider_code: str) -> EmbeddingProvider:
        if provider_code == "dummy":
            return DummyEmbeddingProvider()

        if provider_code == "openai":
            # OpenAIProviderは次フェーズで実装予定
            return DummyEmbeddingProvider()

        return DummyEmbeddingProvider()