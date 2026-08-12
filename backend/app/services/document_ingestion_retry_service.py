from uuid import UUID

from fastapi import status

from app.common.exceptions import AppException, NotFoundException
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.services.embedding_queue_service import EmbeddingQueueService


class DocumentIngestionRetryService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        embedding_job_repository: EmbeddingJobRepository,
        queue_service: EmbeddingQueueService,
    ):
        self.document_repository = document_repository
        self.embedding_job_repository = embedding_job_repository
        self.queue_service = queue_service

    async def retry(self, document_id: UUID) -> dict:
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
        await self.embedding_job_repository.db.commit()

        task_ids = [
            self.queue_service.enqueue(job.id)
            for job in failed_jobs
        ]

        return {
            "document_id": document_id,
            "retried_job_ids": retried_job_ids,
            "task_ids": task_ids,
            "retried_count": len(retried_job_ids),
        }
