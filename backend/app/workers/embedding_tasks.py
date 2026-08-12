import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.models.document import Document  # noqa: F401
from app.models.document_chunk import DocumentChunk  # noqa: F401
from app.models.embedding import Embedding  # noqa: F401
from app.models.embedding_job import EmbeddingJob  # noqa: F401
from app.models.embedding_model import EmbeddingModel  # noqa: F401
from app.models.embedding_provider import EmbeddingProvider  # noqa: F401
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.services.embedding_service import EmbeddingService
from app.workers.celery_app import celery_app


async def _run_embedding_job(job_id: str):
    engine = create_async_engine(
        settings.database_url,
        echo=True,
        poolclass=NullPool,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    try:
        async with session_factory() as db:
            service = EmbeddingService(
                embedding_repository=EmbeddingRepository(db),
                job_repository=EmbeddingJobRepository(db),
                chunk_repository=DocumentChunkRepository(db),
                model_repository=EmbeddingModelRepository(db),
            )
            await service.run_embedding_job(UUID(job_id))
    finally:
        await engine.dispose()


@celery_app.task(name="embedding.run_job")
def run_embedding_job_task(job_id: str):
    asyncio.run(_run_embedding_job(job_id))
    return {"job_id": job_id, "status": "completed"}
