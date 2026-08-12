from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import NotFoundException
from app.services.knowledge_base_document_service import KnowledgeBaseDocumentService


class FakeKnowledgeBaseRepository:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base

    async def find_by_id(self, knowledge_base_id):
        return self.knowledge_base


class FakeDocumentRepository:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def search_by_knowledge_base(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


@pytest.mark.asyncio
async def test_list_documents_searches_documents_with_filters():
    knowledge_base_id = uuid4()
    result = {"items": [], "total": 0, "total_pages": 0}
    document_repository = FakeDocumentRepository(result)
    service = KnowledgeBaseDocumentService(
        knowledge_base_repository=FakeKnowledgeBaseRepository(SimpleNamespace()),
        document_repository=document_repository,
    )

    actual = await service.list_documents(
        knowledge_base_id=knowledge_base_id,
        page=2,
        page_size=10,
        q="商品登録",
        status="active",
        ingestion_status="ready",
        is_latest=True,
        source_type="file",
        sort_by="title",
        sort_order="asc",
    )

    assert actual == result
    assert document_repository.calls == [
        {
            "knowledge_base_id": knowledge_base_id,
            "page": 2,
            "page_size": 10,
            "q": "商品登録",
            "status": "active",
            "ingestion_status": "ready",
            "is_latest": True,
            "source_type": "file",
            "sort_by": "title",
            "sort_order": "asc",
        }
    ]


@pytest.mark.asyncio
async def test_list_documents_raises_when_knowledge_base_missing():
    service = KnowledgeBaseDocumentService(
        knowledge_base_repository=FakeKnowledgeBaseRepository(None),
        document_repository=FakeDocumentRepository(
            {"items": [], "total": 0, "total_pages": 0}
        ),
    )

    with pytest.raises(NotFoundException):
        await service.list_documents(
            knowledge_base_id=uuid4(),
            page=1,
            page_size=20,
            q=None,
            status=None,
            ingestion_status=None,
            is_latest=True,
            source_type=None,
            sort_by="created_at",
            sort_order="desc",
        )
