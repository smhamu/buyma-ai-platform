from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1.document_ingestion import ingest_document
from app.api.v1.document_ingestion import ingest_document_file
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
                knowledge_base_id=payload.knowledge_base_id,
                title=payload.title,
                content=payload.content,
                source_type=payload.source_type,
                source_url=payload.source_url,
                status=payload.status,
                ingestion_status="pending",
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


class FakeUploadFile:
    def __init__(self, filename, content):
        self.filename = filename
        self.content = content

    async def read(self):
        return self.content


class FakeFileIngestionService:
    def __init__(self, jobs):
        self.jobs = jobs

    async def ingest_file(
        self,
        filename,
        file_content,
        embedding_model_id,
        knowledge_base_id=None,
        chunk_size=500,
    ):
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
            "filename": filename,
            "file_size": len(file_content),
            "document": SimpleNamespace(
                id=document_id,
                knowledge_base_id=knowledge_base_id,
                title=filename.rsplit(".", 1)[0],
                content=file_content.decode("utf-8"),
                source_type="file",
                source_url=None,
                status="active",
                ingestion_status="pending",
            ),
            "chunks": chunks,
            "embedding_jobs": self.jobs,
        }


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


@pytest.mark.asyncio
async def test_ingest_document_file_auto_enqueues_created_jobs():
    jobs = [make_job(), make_job()]
    queue_service = FakeQueueService()

    response = await ingest_document_file(
        file=FakeUploadFile("buyma_price.txt", b"content"),
        embedding_model_id=uuid4(),
        knowledge_base_id=uuid4(),
        chunk_size=500,
        auto_enqueue=True,
        service=FakeFileIngestionService(jobs),
        queue_service=queue_service,
        current_user=SimpleNamespace(),
    )

    assert queue_service.enqueued_job_ids == [job.id for job in jobs]
    assert response["message"] == "Document file ingestion completed successfully."
    assert response["data"]["filename"] == "buyma_price.txt"
    assert response["data"]["task_ids"] == ["task-1", "task-2"]


@pytest.mark.asyncio
async def test_ingest_document_file_can_skip_auto_enqueue():
    jobs = [make_job()]
    queue_service = FakeQueueService()

    response = await ingest_document_file(
        file=FakeUploadFile("buyma_shipping.md", b"# content"),
        embedding_model_id=uuid4(),
        knowledge_base_id=None,
        chunk_size=500,
        auto_enqueue=False,
        service=FakeFileIngestionService(jobs),
        queue_service=queue_service,
        current_user=SimpleNamespace(),
    )

    assert queue_service.enqueued_job_ids == []
    assert response["data"]["task_ids"] == []
