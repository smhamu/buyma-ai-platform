from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import AppException, NotFoundException
from app.services.document_ingestion_retry_service import (
    DocumentIngestionRetryService,
)


class FakeDb:
    def __init__(self):
        self.commit_count = 0

    async def commit(self):
        self.commit_count += 1


class FakeDocumentRepository:
    def __init__(self, document):
        self.document = document

    async def find_by_id(self, document_id):
        return self.document


class FakeEmbeddingJobRepository:
    def __init__(self, jobs):
        self.jobs = jobs
        self.db = FakeDb()

    async def find_failed_by_document_id(self, document_id):
        return self.jobs


class FakeQueueService:
    def __init__(self):
        self.enqueued_job_ids = []

    def enqueue(self, job_id):
        self.enqueued_job_ids.append(job_id)
        return f"task-{job_id}"


def make_service(document, jobs):
    queue_service = FakeQueueService()
    embedding_job_repository = FakeEmbeddingJobRepository(jobs)
    service = DocumentIngestionRetryService(
        document_repository=FakeDocumentRepository(document),
        embedding_job_repository=embedding_job_repository,
        queue_service=queue_service,
    )
    return service, embedding_job_repository, queue_service


@pytest.mark.asyncio
async def test_retry_raises_when_document_does_not_exist():
    service, _, _ = make_service(document=None, jobs=[])

    with pytest.raises(NotFoundException) as exc_info:
        await service.retry(uuid4())

    assert exc_info.value.code == "DOCUMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_retry_raises_when_failed_jobs_do_not_exist():
    document = SimpleNamespace(id=uuid4(), ingestion_status="ready")
    service, _, _ = make_service(document=document, jobs=[])

    with pytest.raises(AppException) as exc_info:
        await service.retry(document.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "NO_FAILED_EMBEDDING_JOBS"


@pytest.mark.asyncio
async def test_retry_resets_failed_job_status_and_enqueues_it():
    document = SimpleNamespace(id=uuid4(), ingestion_status="failed")
    job = SimpleNamespace(
        id=uuid4(),
        status="failed",
        error_message="temporary failure",
        retry_count=3,
    )
    service, embedding_job_repository, queue_service = make_service(
        document=document,
        jobs=[job],
    )

    result = await service.retry(document.id)

    assert job.status == "pending"
    assert job.error_message is None
    assert job.retry_count == 3
    assert document.ingestion_status == "pending"
    assert embedding_job_repository.db.commit_count == 1
    assert queue_service.enqueued_job_ids == [job.id]
    assert result["document_id"] == document.id
    assert result["retried_job_ids"] == [job.id]
    assert result["task_ids"] == [f"task-{job.id}"]
    assert result["retried_count"] == 1


@pytest.mark.asyncio
async def test_retry_enqueues_multiple_failed_jobs():
    document = SimpleNamespace(id=uuid4(), ingestion_status="failed")
    jobs = [
        SimpleNamespace(
            id=uuid4(),
            status="failed",
            error_message="first failure",
            retry_count=1,
        ),
        SimpleNamespace(
            id=uuid4(),
            status="failed",
            error_message="second failure",
            retry_count=2,
        ),
    ]
    service, _, queue_service = make_service(document=document, jobs=jobs)

    result = await service.retry(document.id)

    assert [job.status for job in jobs] == ["pending", "pending"]
    assert [job.error_message for job in jobs] == [None, None]
    assert [job.retry_count for job in jobs] == [1, 2]
    assert queue_service.enqueued_job_ids == [job.id for job in jobs]
    assert result["retried_job_ids"] == [job.id for job in jobs]
    assert result["retried_count"] == 2
