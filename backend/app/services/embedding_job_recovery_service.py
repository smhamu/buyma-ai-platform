from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.services.document_ingestion_status_service import (
    DocumentIngestionStatusService,
)


class EmbeddingJobRecoveryService:
    def __init__(
        self,
        db: AsyncSession,
        job_repository: EmbeddingJobRepository,
        document_repository: DocumentRepository,
    ):
        self.db = db
        self.job_repository = job_repository
        self.status_service = DocumentIngestionStatusService(
            document_repository=document_repository,
        )

    async def recover_stale_jobs(
        self,
        *,
        stale_minutes: int = 10,
        limit: int = 100,
    ) -> list:
        stale_before = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)

        if self.db.in_transaction():
            try:
                recovered_jobs = await self.recover_stale_jobs_in_transaction(
                    stale_before=stale_before,
                    limit=limit,
                )
                await self.db.commit()
                return recovered_jobs
            except Exception:
                await self.db.rollback()
                raise

        async with self.db.begin():
            return await self.recover_stale_jobs_in_transaction(
                stale_before=stale_before,
                limit=limit,
            )

    async def recover_stale_jobs_in_transaction(
        self,
        *,
        stale_before: datetime,
        limit: int,
    ) -> list:
        jobs = await self.job_repository.find_stale_processing_jobs(
            stale_before=stale_before,
            limit=limit,
        )

        recovered_jobs = []
        affected_document_ids = set()

        for job in jobs:
            recovered = await self.job_repository.reset_stale_job_to_pending(
                job_id=job.id,
                stale_before=stale_before,
            )
            if not recovered:
                continue

            job.status = "pending"
            job.error_message = "Recovered from stale processing state."
            recovered_jobs.append(job)
            affected_document_ids.add(job.document_id)

        for document_id in affected_document_ids:
            await self.status_service.refresh_status_in_transaction(document_id)

        return recovered_jobs
