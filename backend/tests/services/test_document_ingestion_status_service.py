from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import NotFoundException
from app.services.document_ingestion_status_service import (
    DocumentIngestionStatusService,
)


class FakeScalarResult:
    def __init__(self, statuses):
        self.statuses = statuses

    def all(self):
        return self.statuses


class FakeExecuteResult:
    def __init__(self, statuses):
        self.statuses = statuses

    def scalars(self):
        return FakeScalarResult(self.statuses)


class FakeDb:
    def __init__(self, statuses):
        self.statuses = statuses
        self.commit_count = 0
        self.refreshed = []

    async def execute(self, statement):
        return FakeExecuteResult(self.statuses)

    async def commit(self):
        self.commit_count += 1

    async def refresh(self, obj):
        self.refreshed.append(obj)


class FakeDocumentRepository:
    def __init__(self, document, statuses=None):
        self.document = document
        self.db = FakeDb(statuses or [])

    async def find_by_id(self, document_id):
        return self.document


@pytest.mark.asyncio
async def test_mark_processing_updates_document_status():
    document = SimpleNamespace(id=uuid4(), ingestion_status="pending")
    service = DocumentIngestionStatusService(
        document_repository=FakeDocumentRepository(document)
    )

    result = await service.mark_processing(document.id)

    assert result.ingestion_status == "processing"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "statuses, expected",
    [
        ([], "pending"),
        (["processing", "pending"], "processing"),
        (["completed", "completed"], "ready"),
        (["completed", "failed"], "failed"),
        (["pending", "pending"], "pending"),
    ],
)
async def test_refresh_status_from_embedding_jobs(statuses, expected):
    document = SimpleNamespace(id=uuid4(), ingestion_status="pending")
    service = DocumentIngestionStatusService(
        document_repository=FakeDocumentRepository(document, statuses)
    )

    result = await service.refresh_status(document.id)

    assert result.ingestion_status == expected


@pytest.mark.asyncio
async def test_refresh_status_raises_when_document_does_not_exist():
    service = DocumentIngestionStatusService(
        document_repository=FakeDocumentRepository(None)
    )

    with pytest.raises(NotFoundException):
        await service.refresh_status(uuid4())
