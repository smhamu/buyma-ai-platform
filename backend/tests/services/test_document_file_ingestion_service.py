from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.common.exceptions import AppException, NotFoundException
from app.services.document_file_ingestion_service import (
    DocumentFileIngestionService,
)


class FakeIngestionService:
    def __init__(self):
        self.ingest = AsyncMock(
            return_value={
                "document": SimpleNamespace(id=uuid4()),
                "chunks": [],
                "embedding_jobs": [],
            }
        )


@pytest.mark.asyncio
async def test_ingest_txt_extracts_content_and_calls_ingestion_service():
    ingestion_service = FakeIngestionService()
    service = DocumentFileIngestionService(ingestion_service)
    embedding_model_id = uuid4()
    knowledge_base_id = uuid4()

    result = await service.ingest_file(
        filename="buyma_price.txt",
        file_content="BUYMA価格設定".encode("utf-8"),
        embedding_model_id=embedding_model_id,
        knowledge_base_id=knowledge_base_id,
        chunk_size=500,
    )

    payload = ingestion_service.ingest.await_args.args[0]
    assert payload.title == "buyma_price"
    assert payload.content == "BUYMA価格設定"
    assert payload.source_type == "file"
    assert payload.embedding_model_id == embedding_model_id
    assert payload.knowledge_base_id == knowledge_base_id
    assert result["filename"] == "buyma_price.txt"
    assert result["file_size"] == len("BUYMA価格設定".encode("utf-8"))


@pytest.mark.asyncio
async def test_ingest_markdown_extracts_content():
    ingestion_service = FakeIngestionService()
    service = DocumentFileIngestionService(ingestion_service)

    await service.ingest_file(
        filename="buyma_shipping.md",
        file_content="# BUYMA発送対応".encode("utf-8"),
        embedding_model_id=uuid4(),
    )

    payload = ingestion_service.ingest.await_args.args[0]
    assert payload.title == "buyma_shipping"
    assert payload.content == "# BUYMA発送対応"


@pytest.mark.asyncio
async def test_ingest_rejects_unsupported_extension():
    service = DocumentFileIngestionService(FakeIngestionService())

    with pytest.raises(AppException) as exc_info:
        await service.ingest_file(
            filename="test.xlsx",
            file_content=b"content",
            embedding_model_id=uuid4(),
        )

    assert exc_info.value.status_code == 415
    assert exc_info.value.code == "UNSUPPORTED_DOCUMENT_FILE"


@pytest.mark.asyncio
async def test_ingest_rejects_empty_file():
    service = DocumentFileIngestionService(FakeIngestionService())

    with pytest.raises(AppException) as exc_info:
        await service.ingest_file(
            filename="empty.txt",
            file_content=b"",
            embedding_model_id=uuid4(),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "DOCUMENT_TEXT_EXTRACTION_FAILED"


@pytest.mark.asyncio
async def test_ingest_rejects_large_file():
    service = DocumentFileIngestionService(FakeIngestionService())

    with pytest.raises(AppException) as exc_info:
        await service.ingest_file(
            filename="large.txt",
            file_content=b"a" * (10 * 1024 * 1024 + 1),
            embedding_model_id=uuid4(),
        )

    assert exc_info.value.status_code == 413
    assert exc_info.value.code == "DOCUMENT_FILE_TOO_LARGE"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception",
    [
        NotFoundException("KnowledgeBase"),
        AppException(
            status_code=409,
            code="KNOWLEDGE_BASE_INACTIVE",
            message="Knowledge base is inactive.",
        ),
    ],
)
async def test_ingest_propagates_knowledge_base_errors(exception):
    ingestion_service = FakeIngestionService()
    ingestion_service.ingest.side_effect = exception
    service = DocumentFileIngestionService(ingestion_service)

    with pytest.raises(type(exception)):
        await service.ingest_file(
            filename="buyma.txt",
            file_content=b"content",
            embedding_model_id=uuid4(),
            knowledge_base_id=uuid4(),
        )
