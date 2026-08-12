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


@pytest.mark.asyncio
async def test_ingest_creates_document_chunks_and_embedding_jobs():
    embedding_model_id = uuid4()
    document_repository = FakeRepository()
    chunk_repository = FakeRepository()
    embedding_job_repository = FakeRepository()
    embedding_model_repository = FakeRepository(model=SimpleNamespace())
    service = DocumentIngestionService(
        document_repository=document_repository,
        chunk_repository=chunk_repository,
        embedding_job_repository=embedding_job_repository,
        embedding_model_repository=embedding_model_repository,
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
        document_repository=FakeRepository(),
        chunk_repository=FakeRepository(),
        embedding_job_repository=FakeRepository(),
        embedding_model_repository=FakeRepository(model=None),
    )

    with pytest.raises(NotFoundException):
        await service.ingest(
            DocumentIngestionRequest(
                title="Missing model",
                content="content",
                embedding_model_id=uuid4(),
            )
        )


def test_ingestion_request_validates_chunk_size():
    with pytest.raises(ValidationError):
        DocumentIngestionRequest(
            title="Too small chunk",
            content="content",
            embedding_model_id=uuid4(),
            chunk_size=99,
        )
