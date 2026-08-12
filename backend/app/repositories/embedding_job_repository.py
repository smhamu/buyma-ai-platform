from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding_job import EmbeddingJob
from app.repositories.base_repository import BaseRepository


class EmbeddingJobRepository(BaseRepository[EmbeddingJob]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, EmbeddingJob)

    async def find_by_document_id(self, document_id: UUID) -> list[EmbeddingJob]:
        result = await self.db.execute(
            select(EmbeddingJob)
            .where(EmbeddingJob.document_id == document_id)
            .order_by(EmbeddingJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def find_failed_by_document_id(
        self,
        document_id: UUID,
    ) -> list[EmbeddingJob]:
        result = await self.db.execute(
            select(EmbeddingJob)
            .where(
                EmbeddingJob.document_id == document_id,
                EmbeddingJob.status == "failed",
            )
            .order_by(EmbeddingJob.created_at.asc())
        )
        return list(result.scalars().all())

    async def find_pending(self) -> list[EmbeddingJob]:
        result = await self.db.execute(
            select(EmbeddingJob)
            .where(EmbeddingJob.status == "pending")
            .order_by(EmbeddingJob.created_at.asc())
        )
        return list(result.scalars().all())

    async def find_latest_by_document_id(
        self,
        document_id: UUID,
    ) -> EmbeddingJob | None:
        result = await self.db.execute(
            select(EmbeddingJob)
            .where(EmbeddingJob.document_id == document_id)
            .order_by(EmbeddingJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
