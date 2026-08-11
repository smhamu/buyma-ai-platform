from app.ai.embeddings.factory import EmbeddingProviderFactory
from app.common.exceptions import NotFoundException
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.vector_search import VectorSearchRequest


class VectorSearchService:
    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        model_repository: EmbeddingModelRepository,
    ):
        self.embedding_repository = embedding_repository
        self.model_repository = model_repository

    async def search(self, payload: VectorSearchRequest):
        embedding_model = await self.model_repository.find_by_id_with_provider(
            payload.embedding_model_id
        )

        if embedding_model is None:
            raise NotFoundException("EmbeddingModel")

        provider = EmbeddingProviderFactory.create(
            provider_code=embedding_model.provider.provider_code,
            model_name=embedding_model.model_name,
        )

        query_vector = await provider.generate_embedding(
            text=payload.query,
            dimension=embedding_model.dimension,
        )

        return await self.embedding_repository.vector_search(
            query_vector=query_vector,
            embedding_model_id=payload.embedding_model_id,
            top_k=payload.top_k,
        )