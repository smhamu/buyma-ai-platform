from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AppException, NotFoundException
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository


class DocumentIngestionRetryService:
    def __init__(
        self,
        db: AsyncSession,
        document_repository: DocumentRepository,
        embedding_job_repository: EmbeddingJobRepository,
    ):
        self.db = db
        self.document_repository = document_repository
        self.embedding_job_repository = embedding_job_repository

    async def retry(self, document_id: UUID) -> dict:
        if self.db.in_transaction():
            try:
                result = await self.retry_in_transaction(document_id)
                await self.db.commit()
                return result
            except Exception:
                await self.db.rollback()
                raise

        async with self.db.begin():
            return await self.retry_in_transaction(document_id)

    async def retry_in_transaction(self, document_id: UUID) -> dict:
        document = await self.document_repository.find_by_id(document_id)
        if document is None:
            raise NotFoundException("Document")

        failed_jobs = await self.embedding_job_repository.find_failed_by_document_id(
            document_id
        )
        if not failed_jobs:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="NO_FAILED_EMBEDDING_JOBS",
                message="No failed embedding jobs found.",
            )

        retried_job_ids = []
        for job in failed_jobs:
            job.status = "pending"
            job.error_message = None
            retried_job_ids.append(job.id)

        document.ingestion_status = "pending"

        return {
            "document_id": document_id,
            "retried_job_ids": retried_job_ids,
            "embedding_jobs": failed_jobs,
            "retried_count": len(retried_job_ids),
        }
