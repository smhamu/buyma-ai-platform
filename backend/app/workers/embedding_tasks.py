import asyncio
from uuid import UUID

from celery.exceptions import MaxRetriesExceededError
from app.common.exceptions import (
    AIProviderRateLimitException,
    AIProviderTimeoutException,
    AIProviderUnavailableException,
)
from app.core.config import settings
from app.models.document import Document  # noqa: F401
from app.models.document_chunk import DocumentChunk  # noqa: F401
from app.models.embedding import Embedding  # noqa: F401
from app.models.embedding_job import EmbeddingJob  # noqa: F401
from app.models.embedding_model import EmbeddingModel  # noqa: F401
from app.models.embedding_provider import EmbeddingProvider  # noqa: F401
from app.models.knowledge_base import KnowledgeBase  # noqa: F401
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.services.document_ingestion_status_service import (
    DocumentIngestionStatusService,
)
from app.services.embedding_service import EmbeddingService
from app.workers.celery_app import celery_app
from app.workers.database import create_worker_session

RETRYABLE_EXCEPTIONS = (
    AIProviderRateLimitException,
    AIProviderTimeoutException,
    AIProviderUnavailableException,
)


def is_retryable_exception(exc: Exception) -> bool:
    return isinstance(exc, RETRYABLE_EXCEPTIONS)


async def _create_worker_session():
    return await create_worker_session()


async def _run_embedding_job(job_id: str):
    db, engine = await _create_worker_session()

    try:
        async with db:
            job_repository = EmbeddingJobRepository(db)
            job = await job_repository.find_by_id(UUID(job_id))

            if job is None:
                return

            ingestion_status_service = DocumentIngestionStatusService(
                document_repository=DocumentRepository(db),
            )
            await ingestion_status_service.mark_processing(job.document_id)

            service = EmbeddingService(
                embedding_repository=EmbeddingRepository(db),
                job_repository=job_repository,
                chunk_repository=DocumentChunkRepository(db),
                model_repository=EmbeddingModelRepository(db),
            )
            await service.run_embedding_job(UUID(job_id))
            await ingestion_status_service.refresh_status(job.document_id)
    finally:
        await engine.dispose()


async def _mark_job_for_retry(
    job_id: str,
    retry_count: int,
    error_message: str,
):
    db, engine = await _create_worker_session()

    try:
        async with db:
            repository = EmbeddingJobRepository(db)
            job = await repository.find_by_id(UUID(job_id))

            if job is None:
                return

            job.status = "pending"
            job.retry_count = retry_count
            job.error_message = error_message[:1000]
            await db.commit()
    finally:
        await engine.dispose()


async def _mark_job_failed(
    job_id: str,
    error_message: str,
):
    db, engine = await _create_worker_session()

    try:
        async with db:
            repository = EmbeddingJobRepository(db)
            job = await repository.find_by_id(UUID(job_id))

            if job is None:
                return

            job.status = "failed"
            job.error_message = error_message[:1000]
            document_id = job.document_id
            await db.commit()

            status_service = DocumentIngestionStatusService(
                document_repository=DocumentRepository(db),
            )
            await status_service.refresh_status(document_id)
    finally:
        await engine.dispose()


def _run_embedding_job_task(self, job_id: str):
    try:
        asyncio.run(_run_embedding_job(job_id))
    except Exception as exc:
        if is_retryable_exception(exc):
            retry_number = self.request.retries + 1

            if retry_number > self.max_retries:
                asyncio.run(
                    _mark_job_failed(
                        job_id=job_id,
                        error_message=f"Retry limit exceeded: {exc}",
                    )
                )
                raise

            asyncio.run(
                _mark_job_for_retry(
                    job_id=job_id,
                    retry_count=retry_number,
                    error_message=str(exc),
                )
            )
            countdown = min(2**retry_number * 5, 60)

            try:
                raise self.retry(exc=exc, countdown=countdown)
            except MaxRetriesExceededError:
                asyncio.run(
                    _mark_job_failed(
                        job_id=job_id,
                        error_message=f"Retry limit exceeded: {exc}",
                    )
                )
                raise

        asyncio.run(
            _mark_job_failed(
                job_id=job_id,
                error_message=str(exc),
            )
        )
        raise

    return {"job_id": job_id, "status": "completed"}


@celery_app.task(
    bind=True,
    name="embedding.run_job",
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
)
def run_embedding_job_task(self, job_id: str):
    return _run_embedding_job_task(self, job_id)
