from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding_provider import EmbeddingProvider
from app.repositories.base_repository import BaseRepository


class EmbeddingProviderRepository(BaseRepository[EmbeddingProvider]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, EmbeddingProvider)