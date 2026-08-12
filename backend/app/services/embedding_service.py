from uuid import UUID

from app.ai.embeddings.factory import EmbeddingProviderFactory
from app.common.exceptions import NotFoundException
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository


class EmbeddingService:
    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        job_repository: EmbeddingJobRepository,
        chunk_repository: DocumentChunkRepository,
        model_repository: EmbeddingModelRepository,
    ):
        self.embedding_repository = embedding_repository
        self.job_repository = job_repository
        self.chunk_repository = chunk_repository
        self.model_repository = model_repository

    async def run_embedding_job(self, job_id: UUID):
        job = await self.job_repository.find_by_id(job_id)

        if job is None:
            raise NotFoundException("EmbeddingJob")

        acquired = await self.job_repository.mark_processing_if_pending(job_id)
        if not acquired:
            return None

        await self.job_repository.db.commit()
        await self.job_repository.db.refresh(job)

        chunk = await self.chunk_repository.find_by_id(job.chunk_id)

        if chunk is None:
            raise NotFoundException("DocumentChunk")

        embedding_model = await self.model_repository.find_by_id_with_provider(
            job.embedding_model_id
        )

        if embedding_model is None:
            raise NotFoundException("EmbeddingModel")

        provider_code = embedding_model.provider.provider_code

        provider = EmbeddingProviderFactory.create(
            provider_code=provider_code,
            model_name=embedding_model.model_name,
        )

        vector = await provider.generate_embedding(
            text=chunk.content,
            dimension=embedding_model.dimension,
        )

        embedding = await self.embedding_repository.create(
            {
                "document_id": job.document_id,
                "chunk_id": job.chunk_id,
                "embedding_model_id": job.embedding_model_id,
                "embedding_job_id": job.id,
                "vector": vector,
                "dimension": embedding_model.dimension,
                "status": "active",
                "metadata_text": f"{provider_code} embedding for chunk {chunk.id}",
            }
        )

        job.status = "completed"
        job.error_message = None
        await self.job_repository.db.commit()
        await self.job_repository.db.refresh(job)

        return embedding

    async def list_embeddings(self):
        return await self.embedding_repository.find_all()

    async def get_embedding(self, embedding_id: UUID):
        embedding = await self.embedding_repository.find_by_id(embedding_id)

        if embedding is None:
            raise NotFoundException("Embedding")

        return embedding

    async def list_chunk_embeddings(self, chunk_id: UUID):
        chunk = await self.chunk_repository.find_by_id(chunk_id)

        if chunk is None:
            raise NotFoundException("DocumentChunk")

        return await self.embedding_repository.find_by_chunk_id(chunk_id)
