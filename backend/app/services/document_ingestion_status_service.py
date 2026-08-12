from uuid import UUID

from sqlalchemy import select

from app.common.exceptions import NotFoundException
from app.models.embedding_job import EmbeddingJob
from app.repositories.document_repository import DocumentRepository


class DocumentIngestionStatusService:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def mark_processing(self, document_id: UUID):
        document = await self.document_repository.find_by_id(document_id)

        if document is None:
            raise NotFoundException("Document")

        document.ingestion_status = "processing"
        await self.document_repository.db.commit()
        await self.document_repository.db.refresh(document)

        return document

    async def refresh_status(self, document_id: UUID):
        document = await self.document_repository.find_by_id(document_id)

        if document is None:
            raise NotFoundException("Document")

        result = await self.document_repository.db.execute(
            select(EmbeddingJob.status).where(
                EmbeddingJob.document_id == document_id
            )
        )
        statuses = list(result.scalars().all())

        if not statuses:
            document.ingestion_status = "pending"
        elif "failed" in statuses:
            document.ingestion_status = "failed"
        elif all(status == "completed" for status in statuses):
            document.ingestion_status = "ready"
        elif any(status == "processing" for status in statuses):
            document.ingestion_status = "processing"
        else:
            document.ingestion_status = "pending"

        await self.document_repository.db.commit()
        await self.document_repository.db.refresh(document)

        return document
