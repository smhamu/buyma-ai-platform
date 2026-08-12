from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
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

    async def mark_processing_if_pending(
        self,
        job_id: UUID,
    ) -> bool:
        result = await self.db.execute(
            update(EmbeddingJob)
            .where(
                EmbeddingJob.id == job_id,
                EmbeddingJob.status == "pending",
            )
            .values(
                status="processing",
                error_message=None,
            )
        )
        await self.db.flush()
        return result.rowcount == 1

    async def find_stale_processing_jobs(
        self,
        stale_before: datetime,
        limit: int = 100,
    ) -> list[EmbeddingJob]:
        result = await self.db.execute(
            select(EmbeddingJob)
            .where(
                EmbeddingJob.status == "processing",
                EmbeddingJob.updated_at < stale_before,
            )
            .order_by(EmbeddingJob.updated_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def reset_stale_job_to_pending(
        self,
        job_id: UUID,
        stale_before: datetime,
    ) -> bool:
        result = await self.db.execute(
            update(EmbeddingJob)
            .where(
                EmbeddingJob.id == job_id,
                EmbeddingJob.status == "processing",
                EmbeddingJob.updated_at < stale_before,
            )
            .values(
                status="pending",
                error_message="Recovered from stale processing state.",
            )
        )
        await self.db.flush()
        return result.rowcount == 1
