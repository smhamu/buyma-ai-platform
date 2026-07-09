from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding import Embedding
from app.repositories.base_repository import BaseRepository


class EmbeddingRepository(BaseRepository[Embedding]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Embedding)

    async def find_by_chunk_id(self, chunk_id: UUID) -> list[Embedding]:
        result = await self.db.execute(
            select(Embedding)
            .where(Embedding.chunk_id == chunk_id)
            .order_by(Embedding.created_at.desc())
        )
        return list(result.scalars().all())