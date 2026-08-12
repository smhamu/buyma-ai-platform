from uuid import UUID

from fastapi import status

from app.common.exceptions import AppException, NotFoundException
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.schemas.document_ingestion import DocumentIngestionRequest
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.embedding_queue_service import EmbeddingQueueService


class DocumentVersionRollbackService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        embedding_job_repository: EmbeddingJobRepository,
        ingestion_service: DocumentIngestionService,
        queue_service: EmbeddingQueueService,
    ):
        self.document_repository = document_repository
        self.embedding_job_repository = embedding_job_repository
        self.ingestion_service = ingestion_service
        self.queue_service = queue_service

    async def restore(self, document_id: UUID):
        source_document = await self.document_repository.find_by_id(document_id)
        if source_document is None:
            raise NotFoundException("Document")

        latest_document = await self.document_repository.find_latest_by_version_group(
            source_document.version_group_id
        )
        if latest_document is None:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="DOCUMENT_VERSION_STATE_INVALID",
                message="Latest document version could not be determined.",
            )

        if source_document.is_latest:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="DOCUMENT_VERSION_ALREADY_LATEST",
                message="The selected document version is already the latest.",
            )

        if latest_document.ingestion_status in {"pending", "processing"}:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="DOCUMENT_INGESTION_IN_PROGRESS",
                message=(
                    "Document version cannot be restored while the latest "
                    "version is being ingested."
                ),
            )

        latest_job = await self.embedding_job_repository.find_latest_by_document_id(
            latest_document.id
        )
        if latest_job is None:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="EMBEDDING_MODEL_NOT_RESOLVED",
                message="Embedding model could not be resolved for rollback.",
            )

        result = await self.ingestion_service.ingest(
            DocumentIngestionRequest(
                knowledge_base_id=source_document.knowledge_base_id,
                title=source_document.title,
                content=source_document.content,
                source_type=source_document.source_type,
                source_url=source_document.source_url,
                original_filename=source_document.original_filename,
                mime_type=source_document.mime_type,
                file_size=source_document.file_size,
                checksum=source_document.checksum,
                version=latest_document.version + 1,
                previous_document_id=latest_document.id,
                version_group_id=source_document.version_group_id,
                is_latest=True,
                status=source_document.status,
                embedding_model_id=latest_job.embedding_model_id,
                chunk_size=500,
                auto_enqueue=False,
            )
        )

        latest_document.is_latest = False
        await self.document_repository.db.commit()

        task_ids = [
            self.queue_service.enqueue(job.id)
            for job in result["embedding_jobs"]
        ]

        return {
            "restored_from_document_id": source_document.id,
            "restored_from_version": source_document.version,
            "new_document": result["document"],
            "task_ids": task_ids,
        }
