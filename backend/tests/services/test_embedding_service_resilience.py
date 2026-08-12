from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.embedding_service import EmbeddingService


class FakeDb:
    def __init__(self):
        self.commit_count = 0
        self.refreshes = []

    async def commit(self):
        self.commit_count += 1

    async def refresh(self, obj):
        self.refreshes.append(obj)


class FakeJobRepository:
    def __init__(self, job, acquired):
        self.job = job
        self.acquired = acquired
        self.db = FakeDb()
        self.acquire_calls = []

    async def find_by_id(self, job_id):
        return self.job

    async def mark_processing_if_pending(self, job_id):
        self.acquire_calls.append(job_id)
        if self.acquired:
            self.job.status = "processing"
        return self.acquired


class FakeRepository:
    def __init__(self, obj=None):
        self.obj = obj
        self.created = []

    async def find_by_id(self, obj_id):
        return self.obj

    async def find_by_id_with_provider(self, obj_id):
        return self.obj

    async def create(self, data):
        obj = SimpleNamespace(id=uuid4(), **data)
        self.created.append(obj)
        return obj


class FakeProvider:
    async def generate_embedding(self, text, dimension):
        return [0.1] * dimension


@pytest.mark.asyncio
async def test_run_embedding_job_skips_when_job_is_not_pending():
    job = SimpleNamespace(id=uuid4(), status="processing")
    job_repository = FakeJobRepository(job=job, acquired=False)
    service = EmbeddingService(
        embedding_repository=FakeRepository(),
        job_repository=job_repository,
        chunk_repository=FakeRepository(),
        model_repository=FakeRepository(),
    )

    result = await service.run_embedding_job(job.id)

    assert result is None
    assert job_repository.acquire_calls == [job.id]
    assert job_repository.db.commit_count == 0


@pytest.mark.asyncio
async def test_run_embedding_job_acquires_pending_job_and_completes(monkeypatch):
    from app.services import embedding_service as module

    job = SimpleNamespace(
        id=uuid4(),
        document_id=uuid4(),
        chunk_id=uuid4(),
        embedding_model_id=uuid4(),
        status="pending",
        error_message="old error",
    )
    chunk = SimpleNamespace(id=job.chunk_id, content="chunk content")
    model = SimpleNamespace(
        id=job.embedding_model_id,
        dimension=3,
        model_name="dummy",
        provider=SimpleNamespace(provider_code="dummy"),
    )
    embedding_repository = FakeRepository()
    job_repository = FakeJobRepository(job=job, acquired=True)
    service = EmbeddingService(
        embedding_repository=embedding_repository,
        job_repository=job_repository,
        chunk_repository=FakeRepository(chunk),
        model_repository=FakeRepository(model),
    )
    monkeypatch.setattr(
        module.EmbeddingProviderFactory,
        "create",
        lambda provider_code, model_name: FakeProvider(),
    )

    embedding = await service.run_embedding_job(job.id)

    assert embedding in embedding_repository.created
    assert job.status == "completed"
    assert job.error_message is None
    assert job_repository.db.commit_count == 2
