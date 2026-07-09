from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding_model import EmbeddingModel
from app.repositories.base_repository import BaseRepository


class EmbeddingModelRepository(BaseRepository[EmbeddingModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, EmbeddingModel)