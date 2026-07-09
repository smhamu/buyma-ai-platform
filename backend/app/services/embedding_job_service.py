from uuid import UUID

from app.common.exceptions import NotFoundException
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository


class EmbeddingJobService:
    def __init__(
        self,
        job_repository: EmbeddingJobRepository,
        document_repository: DocumentRepository,
        chunk_repository: DocumentChunkRepository,
        model_repository: EmbeddingModelRepository,
    ):
        self.job_repository = job_repository
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.model_repository = model_repository

    async def generate_jobs_for_document(
        self,
        document_id: UUID,
        embedding_model_id: UUID,
    ):
        document = await self.document_repository.find_by_id(document_id)

        if document is None:
            raise NotFoundException("Document")

        embedding_model = await self.model_repository.find_by_id(embedding_model_id)

        if embedding_model is None:
            raise NotFoundException("EmbeddingModel")

        chunks = await self.chunk_repository.find_by_document_id(document_id)

        if not chunks:
            raise NotFoundException("DocumentChunk")

        created_jobs = []

        for chunk in chunks:
            job = await self.job_repository.create(
                {
                    "document_id": document_id,
                    "chunk_id": chunk.id,
                    "embedding_model_id": embedding_model_id,
                    "status": "pending",
                    "retry_count": 0,
                }
            )
            created_jobs.append(job)

        return created_jobs

    async def list_jobs(self):
        return await self.job_repository.find_all()

    async def get_job(self, job_id: UUID):
        job = await self.job_repository.find_by_id(job_id)

        if job is None:
            raise NotFoundException("EmbeddingJob")

        return job

    async def list_document_jobs(self, document_id: UUID):
        document = await self.document_repository.find_by_id(document_id)

        if document is None:
            raise NotFoundException("Document")

        return await self.job_repository.find_by_document_id(document_id)