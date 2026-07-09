from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.embedding_model import EmbeddingModel
from app.repositories.base_repository import BaseRepository


class EmbeddingModelRepository(BaseRepository[EmbeddingModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, EmbeddingModel)

    async def find_by_id_with_provider(
        self,
        model_id: UUID,
    ) -> EmbeddingModel | None:
        result = await self.db.execute(
            select(EmbeddingModel)
            .where(EmbeddingModel.id == model_id)
            .options(selectinload(EmbeddingModel.provider))
        )
        return result.scalar_one_or_none()