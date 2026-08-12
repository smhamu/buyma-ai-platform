from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import AppException, NotFoundException
from app.services.document_version_rollback_service import (
    DocumentVersionRollbackService,
)


def make_document(**overrides):
    data = {
        "id": uuid4(),
        "knowledge_base_id": uuid4(),
        "title": "rule",
        "content": "content",
        "source_type": "file",
        "source_url": None,
        "original_filename": "rule.txt",
        "mime_type": "text/plain",
        "file_size": 10,
        "checksum": "a" * 64,
        "version": 1,
        "previous_document_id": None,
        "version_group_id": uuid4(),
        "is_latest": False,
        "status": "active",
        "ingestion_status": "ready",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class FakeDb:
    def __init__(self):
        self.commit_count = 0

    async def commit(self):
        self.commit_count += 1


class FakeDocumentRepository:
    def __init__(self, source_document, latest_document):
        self.source_document = source_document
        self.latest_document = latest_document
        self.db = FakeDb()

    async def find_by_id(self, document_id):
        return self.source_document

    async def find_latest_by_version_group(self, version_group_id):
        return self.latest_document


class FakeEmbeddingJobRepository:
    def __init__(self, job):
        self.job = job

    async def find_latest_by_document_id(self, document_id):
        return self.job


class FakeIngestionService:
    def __init__(self, new_document, jobs):
        self.new_document = new_document
        self.jobs = jobs
        self.payloads = []

    async def ingest(self, payload):
        self.payloads.append(payload)
        return {
            "document": self.new_document,
            "chunks": [],
            "embedding_jobs": self.jobs,
        }


class FakeQueueService:
    def __init__(self):
        self.enqueued_job_ids = []

    def enqueue(self, job_id):
        self.enqueued_job_ids.append(job_id)
        return f"task-{job_id}"


def make_service(
    source_document,
    latest_document,
    latest_job,
    new_document=None,
    jobs=None,
):
    queue_service = FakeQueueService()
    ingestion_service = FakeIngestionService(
        new_document=new_document or make_document(version=3, is_latest=True),
        jobs=jobs or [],
    )
    document_repository = FakeDocumentRepository(
        source_document=source_document,
        latest_document=latest_document,
    )
    service = DocumentVersionRollbackService(
        document_repository=document_repository,
        embedding_job_repository=FakeEmbeddingJobRepository(latest_job),
        ingestion_service=ingestion_service,
        queue_service=queue_service,
    )
    return service, document_repository, ingestion_service, queue_service


@pytest.mark.asyncio
async def test_restore_old_version_creates_new_latest_version_and_enqueues_jobs():
    version_group_id = uuid4()
    embedding_model_id = uuid4()
    source = make_document(
        version=1,
        content="v1 content",
        version_group_id=version_group_id,
        is_latest=False,
    )
    latest = make_document(
        version=2,
        content="v2 content",
        version_group_id=version_group_id,
        is_latest=True,
    )
    new_document = make_document(
        version=3,
        content="v1 content",
        version_group_id=version_group_id,
        previous_document_id=latest.id,
        is_latest=True,
    )
    jobs = [
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(id=uuid4()),
    ]
    service, repository, ingestion_service, queue_service = make_service(
        source_document=source,
        latest_document=latest,
        latest_job=SimpleNamespace(embedding_model_id=embedding_model_id),
        new_document=new_document,
        jobs=jobs,
    )

    result = await service.restore(source.id)

    payload = ingestion_service.payloads[0]
    assert payload.content == "v1 content"
    assert payload.version == 3
    assert payload.previous_document_id == latest.id
    assert payload.version_group_id == version_group_id
    assert payload.embedding_model_id == embedding_model_id
    assert payload.original_filename == source.original_filename
    assert payload.checksum == source.checksum
    assert latest.is_latest is False
    assert repository.db.commit_count == 1
    assert queue_service.enqueued_job_ids == [job.id for job in jobs]
    assert result["restored_from_document_id"] == source.id
    assert result["restored_from_version"] == 1
    assert result["new_document"] == new_document
    assert result["task_ids"] == [f"task-{job.id}" for job in jobs]


@pytest.mark.asyncio
async def test_restore_raises_when_document_does_not_exist():
    service, _, _, _ = make_service(
        source_document=None,
        latest_document=None,
        latest_job=None,
    )

    with pytest.raises(NotFoundException):
        await service.restore(uuid4())


@pytest.mark.asyncio
async def test_restore_raises_when_latest_version_missing():
    source = make_document(is_latest=False)
    service, _, _, _ = make_service(
        source_document=source,
        latest_document=None,
        latest_job=None,
    )

    with pytest.raises(AppException) as exc_info:
        await service.restore(source.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "DOCUMENT_VERSION_STATE_INVALID"


@pytest.mark.asyncio
async def test_restore_rejects_latest_version():
    source = make_document(is_latest=True)
    service, _, _, _ = make_service(
        source_document=source,
        latest_document=source,
        latest_job=SimpleNamespace(embedding_model_id=uuid4()),
    )

    with pytest.raises(AppException) as exc_info:
        await service.restore(source.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "DOCUMENT_VERSION_ALREADY_LATEST"


@pytest.mark.asyncio
@pytest.mark.parametrize("ingestion_status", ["pending", "processing"])
async def test_restore_rejects_when_latest_ingestion_is_in_progress(
    ingestion_status,
):
    version_group_id = uuid4()
    source = make_document(version_group_id=version_group_id, is_latest=False)
    latest = make_document(
        version_group_id=version_group_id,
        is_latest=True,
        ingestion_status=ingestion_status,
    )
    service, _, _, _ = make_service(
        source_document=source,
        latest_document=latest,
        latest_job=SimpleNamespace(embedding_model_id=uuid4()),
    )

    with pytest.raises(AppException) as exc_info:
        await service.restore(source.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "DOCUMENT_INGESTION_IN_PROGRESS"


@pytest.mark.asyncio
async def test_restore_raises_when_embedding_model_cannot_be_resolved():
    version_group_id = uuid4()
    source = make_document(version_group_id=version_group_id, is_latest=False)
    latest = make_document(version_group_id=version_group_id, is_latest=True)
    service, _, _, _ = make_service(
        source_document=source,
        latest_document=latest,
        latest_job=None,
    )

    with pytest.raises(AppException) as exc_info:
        await service.restore(source.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "EMBEDDING_MODEL_NOT_RESOLVED"
