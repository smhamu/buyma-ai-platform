from uuid import UUID

from app.workers.embedding_tasks import run_embedding_job_task


class EmbeddingQueueService:
    def enqueue(self, job_id: UUID) -> str:
        task = run_embedding_job_task.delay(str(job_id))
        return task.id
