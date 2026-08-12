from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.common.exceptions import NotFoundException
from app.schemas.document_ingestion import DocumentIngestionRequest
from app.services.document_ingestion_service import DocumentIngestionService


class FakeRepository:
    def __init__(self, model=None):
        self.model = model
        self.created = []

    async def find_by_id(self, obj_id):
        return self.model

    async def create(self, data):
        obj = SimpleNamespace(id=uuid4(), **data)
        self.created.append(obj)
        return obj

    async def create_without_commit(self, data):
        return await self.create(data)


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeDb:
    def in_transaction(self):
        return False

    def begin(self):
        return FakeTransaction()


@pytest.mark.asyncio
async def test_ingest_creates_document_chunks_and_embedding_jobs():
    embedding_model_id = uuid4()
    document_repository = FakeRepository()
    chunk_repository = FakeRepository()
    embedding_job_repository = FakeRepository()
    embedding_model_repository = FakeRepository(model=SimpleNamespace())
    service = DocumentIngestionService(
        db=FakeDb(),
        document_repository=document_repository,
        chunk_repository=chunk_repository,
        embedding_job_repository=embedding_job_repository,
        embedding_model_repository=embedding_model_repository,
        knowledge_base_repository=FakeRepository(),
    )

    result = await service.ingest(
        DocumentIngestionRequest(
            title="BUYMA返品対応",
            content="a" * 250,
            embedding_model_id=embedding_model_id,
            chunk_size=100,
        )
    )

    assert result["document"].title == "BUYMA返品対応"
    assert len(result["chunks"]) == 3
    assert len(result["embedding_jobs"]) == 3
    assert [chunk.chunk_index for chunk in result["chunks"]] == [0, 1, 2]
    assert all(job.status == "pending" for job in result["embedding_jobs"])
    assert all(job.retry_count == 0 for job in result["embedding_jobs"])
    assert all(
        job.embedding_model_id == embedding_model_id
        for job in result["embedding_jobs"]
    )


@pytest.mark.asyncio
async def test_ingest_raises_when_embedding_model_does_not_exist():
    service = DocumentIngestionService(
        db=FakeDb(),
        document_repository=FakeRepository(),
        chunk_repository=FakeRepository(),
        embedding_job_repository=FakeRepository(),
        embedding_model_repository=FakeRepository(model=None),
        knowledge_base_repository=FakeRepository(),
    )

    with pytest.raises(NotFoundException):
        await service.ingest(
            DocumentIngestionRequest(
                title="Missing model",
                content="content",
                embedding_model_id=uuid4(),
            )
        )


@pytest.mark.asyncio
async def test_ingest_raises_when_knowledge_base_does_not_exist():
    service = DocumentIngestionService(
        db=FakeDb(),
        document_repository=FakeRepository(),
        chunk_repository=FakeRepository(),
        embedding_job_repository=FakeRepository(),
        embedding_model_repository=FakeRepository(model=SimpleNamespace()),
        knowledge_base_repository=FakeRepository(model=None),
    )

    with pytest.raises(NotFoundException) as exc_info:
        await service.ingest(
            DocumentIngestionRequest(
                knowledge_base_id=uuid4(),
                title="Missing KB",
                content="content",
                embedding_model_id=uuid4(),
            )
        )

    assert exc_info.value.code == "KNOWLEDGEBASE_NOT_FOUND"


@pytest.mark.asyncio
async def test_ingest_raises_when_knowledge_base_is_inactive():
    service = DocumentIngestionService(
        db=FakeDb(),
        document_repository=FakeRepository(),
        chunk_repository=FakeRepository(),
        embedding_job_repository=FakeRepository(),
        embedding_model_repository=FakeRepository(model=SimpleNamespace()),
        knowledge_base_repository=FakeRepository(
            model=SimpleNamespace(is_active=False)
        ),
    )

    with pytest.raises(Exception) as exc_info:
        await service.ingest(
            DocumentIngestionRequest(
                knowledge_base_id=uuid4(),
                title="Inactive KB",
                content="content",
                embedding_model_id=uuid4(),
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "KNOWLEDGE_BASE_INACTIVE"


def test_ingestion_request_validates_chunk_size():
    with pytest.raises(ValidationError):
        DocumentIngestionRequest(
            title="Too small chunk",
            content="content",
            embedding_model_id=uuid4(),
            chunk_size=99,
        )
