from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1.document_ingestion import ingest_document
from app.schemas.document_ingestion import DocumentIngestionRequest


class FakeIngestionService:
    def __init__(self, jobs):
        self.jobs = jobs

    async def ingest(self, payload):
        document_id = uuid4()
        chunks = [
            SimpleNamespace(
                id=job.chunk_id,
                document_id=document_id,
                chunk_index=index,
                content=f"chunk-{index}",
            )
            for index, job in enumerate(self.jobs)
        ]
        return {
            "document": SimpleNamespace(
                id=document_id,
                title=payload.title,
                content=payload.content,
                source_type=payload.source_type,
                source_url=payload.source_url,
                status=payload.status,
            ),
            "chunks": chunks,
            "embedding_jobs": self.jobs,
        }


class FakeQueueService:
    def __init__(self):
        self.enqueued_job_ids = []

    def enqueue(self, job_id):
        self.enqueued_job_ids.append(job_id)
        return f"task-{len(self.enqueued_job_ids)}"


def make_job():
    return SimpleNamespace(
        id=uuid4(),
        document_id=uuid4(),
        chunk_id=uuid4(),
        embedding_model_id=uuid4(),
        status="pending",
        retry_count=0,
        error_message=None,
    )


@pytest.mark.asyncio
async def test_ingest_document_auto_enqueues_created_jobs():
    jobs = [make_job(), make_job()]
    queue_service = FakeQueueService()

    response = await ingest_document(
        payload=DocumentIngestionRequest(
            title="Queue Test",
            content="content",
            embedding_model_id=uuid4(),
        ),
        service=FakeIngestionService(jobs),
        queue_service=queue_service,
        current_user=SimpleNamespace(),
    )

    assert queue_service.enqueued_job_ids == [job.id for job in jobs]
    assert response["data"]["task_ids"] == ["task-1", "task-2"]


@pytest.mark.asyncio
async def test_ingest_document_can_skip_auto_enqueue():
    jobs = [make_job()]
    queue_service = FakeQueueService()

    response = await ingest_document(
        payload=DocumentIngestionRequest(
            title="Queue Test",
            content="content",
            embedding_model_id=uuid4(),
            auto_enqueue=False,
        ),
        service=FakeIngestionService(jobs),
        queue_service=queue_service,
        current_user=SimpleNamespace(),
    )

    assert queue_service.enqueued_job_ids == []
    assert response["data"]["task_ids"] == []
    assert response["data"]["embedding_jobs"][0]["status"] == "pending"
