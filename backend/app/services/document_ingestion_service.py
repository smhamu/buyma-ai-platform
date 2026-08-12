from uuid import uuid4

from fastapi import status

from app.common.exceptions import AppException, NotFoundException
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.document_ingestion import DocumentIngestionRequest


class DocumentIngestionService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: DocumentChunkRepository,
        embedding_job_repository: EmbeddingJobRepository,
        embedding_model_repository: EmbeddingModelRepository,
        knowledge_base_repository: KnowledgeBaseRepository,
    ):
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.embedding_job_repository = embedding_job_repository
        self.embedding_model_repository = embedding_model_repository
        self.knowledge_base_repository = knowledge_base_repository

    async def ingest(self, payload: DocumentIngestionRequest):
        if payload.knowledge_base_id is not None:
            knowledge_base = await self.knowledge_base_repository.find_by_id(
                payload.knowledge_base_id
            )

            if knowledge_base is None:
                raise NotFoundException("KnowledgeBase")

            if not knowledge_base.is_active:
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="KNOWLEDGE_BASE_INACTIVE",
                    message="Knowledge base is inactive.",
                )

        embedding_model = await self.embedding_model_repository.find_by_id(
            payload.embedding_model_id
        )

        if embedding_model is None:
            raise NotFoundException("EmbeddingModel")

        document = await self.document_repository.create(
            {
                "knowledge_base_id": payload.knowledge_base_id,
                "title": payload.title,
                "content": payload.content,
                "source_type": payload.source_type,
                "source_url": payload.source_url,
                "original_filename": payload.original_filename,
                "mime_type": payload.mime_type,
                "file_size": payload.file_size,
                "checksum": payload.checksum,
                "version": payload.version,
                "previous_document_id": payload.previous_document_id,
                "version_group_id": payload.version_group_id or uuid4(),
                "is_latest": payload.is_latest,
                "status": payload.status,
                "ingestion_status": "pending",
            }
        )

        created_chunks = []
        for index, content in enumerate(
            self._split_text(document.content, payload.chunk_size)
        ):
            chunk = await self.chunk_repository.create(
                {
                    "document_id": document.id,
                    "chunk_index": index,
                    "content": content,
                }
            )
            created_chunks.append(chunk)

        created_jobs = []
        for chunk in created_chunks:
            job = await self.embedding_job_repository.create(
                {
                    "document_id": document.id,
                    "chunk_id": chunk.id,
                    "embedding_model_id": payload.embedding_model_id,
                    "status": "pending",
                    "retry_count": 0,
                }
            )
            created_jobs.append(job)

        return {
            "document": document,
            "chunks": created_chunks,
            "embedding_jobs": created_jobs,
        }

    @staticmethod
    def _split_text(text: str, chunk_size: int) -> list[str]:
        return [
            text[i : i + chunk_size]
            for i in range(0, len(text), chunk_size)
            if text[i : i + chunk_size].strip()
        ]
