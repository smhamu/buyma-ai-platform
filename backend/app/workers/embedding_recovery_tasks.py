import asyncio
from uuid import UUID

from app.core.config import settings
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.services.embedding_job_recovery_service import EmbeddingJobRecoveryService
from app.services.embedding_queue_service import EmbeddingQueueService
from app.workers.celery_app import celery_app
from app.workers.database import create_worker_session


async def _recover_stale_jobs():
    db, engine = await create_worker_session()

    try:
        async with db:
            service = EmbeddingJobRecoveryService(
                db=db,
                job_repository=EmbeddingJobRepository(db),
                document_repository=DocumentRepository(db),
            )
            jobs = await service.recover_stale_jobs(
                stale_minutes=settings.embedding_job_stale_minutes,
                limit=settings.embedding_recovery_batch_size,
            )
            return [str(job.id) for job in jobs]
    finally:
        await engine.dispose()


@celery_app.task(name="embedding.recover_stale_jobs")
def recover_stale_jobs_task():
    job_ids = asyncio.run(_recover_stale_jobs())
    queue_service = EmbeddingQueueService()

    task_ids = []
    for job_id in job_ids:
        task_ids.append(queue_service.enqueue(UUID(job_id)))

    return {
        "recovered_count": len(job_ids),
        "job_ids": job_ids,
        "task_ids": task_ids,
    }
