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


class FakeDocumentRepository:
    def __init__(self, existing_document=None):
        self.existing_document = existing_document
        self.find_by_checksum_calls = []

    async def find_by_checksum(self, checksum, knowledge_base_id=None):
        self.find_by_checksum_calls.append(
            {
                "checksum": checksum,
                "knowledge_base_id": knowledge_base_id,
            }
        )
        return self.existing_document


def make_service(ingestion_service=None, existing_document=None):
    return DocumentFileIngestionService(
        ingestion_service=ingestion_service or FakeIngestionService(),
        document_repository=FakeDocumentRepository(existing_document),
    )


@pytest.mark.asyncio
async def test_ingest_txt_extracts_content_and_calls_ingestion_service():
    ingestion_service = FakeIngestionService()
    document_repository = FakeDocumentRepository()
    service = DocumentFileIngestionService(
        ingestion_service=ingestion_service,
        document_repository=document_repository,
    )
    embedding_model_id = uuid4()
    knowledge_base_id = uuid4()
    content_bytes = "BUYMA価格設定".encode("utf-8")

    result = await service.ingest_file(
        filename="buyma_price.txt",
        file_content=content_bytes,
        embedding_model_id=embedding_model_id,
        mime_type="text/plain",
        knowledge_base_id=knowledge_base_id,
        chunk_size=500,
    )

    payload = ingestion_service.ingest.await_args.args[0]
    assert payload.title == "buyma_price"
    assert payload.content == "BUYMA価格設定"
    assert payload.source_type == "file"
    assert payload.original_filename == "buyma_price.txt"
    assert payload.mime_type == "text/plain"
    assert payload.file_size == len(content_bytes)
    assert len(payload.checksum) == 64
    assert payload.embedding_model_id == embedding_model_id
    assert payload.knowledge_base_id == knowledge_base_id
    assert document_repository.find_by_checksum_calls == [
        {
            "checksum": payload.checksum,
            "knowledge_base_id": knowledge_base_id,
        }
    ]
    assert result["filename"] == "buyma_price.txt"
    assert result["file_size"] == len(content_bytes)


@pytest.mark.asyncio
async def test_ingest_markdown_extracts_content():
    ingestion_service = FakeIngestionService()
    service = make_service(ingestion_service)

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
    service = make_service()

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
    service = make_service()

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
    service = make_service()

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
    service = make_service(ingestion_service)

    with pytest.raises(type(exception)):
        await service.ingest_file(
            filename="buyma.txt",
            file_content=b"content",
            embedding_model_id=uuid4(),
            knowledge_base_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_ingest_rejects_duplicate_file_in_same_knowledge_base():
    knowledge_base_id = uuid4()
    service = make_service(existing_document=SimpleNamespace(id=uuid4()))

    with pytest.raises(AppException) as exc_info:
        await service.ingest_file(
            filename="buyma.txt",
            file_content=b"content",
            embedding_model_id=uuid4(),
            knowledge_base_id=knowledge_base_id,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "DUPLICATE_DOCUMENT_FILE"


@pytest.mark.asyncio
async def test_same_file_can_be_registered_when_repository_returns_no_duplicate():
    ingestion_service = FakeIngestionService()
    service = make_service(ingestion_service=ingestion_service)

    await service.ingest_file(
        filename="buyma.txt",
        file_content=b"content",
        embedding_model_id=uuid4(),
        knowledge_base_id=uuid4(),
    )

    ingestion_service.ingest.assert_awaited_once()
