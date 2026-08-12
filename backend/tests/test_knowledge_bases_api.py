from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.knowledge_bases import (
    create_knowledge_base,
    delete_knowledge_base,
    get_knowledge_base,
    list_knowledge_base_documents,
)
from app.schemas.knowledge_base import KnowledgeBaseCreate


def make_knowledge_base(**overrides):
    data = {
        "id": uuid4(),
        "name": "BUYMA出品ナレッジ",
        "description": "出品関連情報",
        "is_active": True,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.asyncio
async def test_create_knowledge_base_returns_response():
    knowledge_base = make_knowledge_base()
    service = SimpleNamespace(create=AsyncMock(return_value=knowledge_base))

    response = await create_knowledge_base(
        payload=KnowledgeBaseCreate(
            name=knowledge_base.name,
            description=knowledge_base.description,
        ),
        service=service,
        current_user=SimpleNamespace(),
    )

    assert response["success"] is True
    assert response["data"].id == knowledge_base.id
    assert response["data"].name == knowledge_base.name


@pytest.mark.asyncio
async def test_get_knowledge_base_returns_response():
    knowledge_base = make_knowledge_base()
    service = SimpleNamespace(get=AsyncMock(return_value=knowledge_base))

    response = await get_knowledge_base(
        knowledge_base_id=knowledge_base.id,
        service=service,
        current_user=SimpleNamespace(),
    )

    service.get.assert_awaited_once_with(knowledge_base.id)
    assert response["data"].id == knowledge_base.id


@pytest.mark.asyncio
async def test_delete_knowledge_base_returns_deleted_id():
    knowledge_base_id = uuid4()
    service = SimpleNamespace(
        delete=AsyncMock(return_value={"id": str(knowledge_base_id)})
    )

    response = await delete_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        service=service,
        current_user=SimpleNamespace(),
    )

    assert response["data"] == {"id": str(knowledge_base_id)}


@pytest.mark.asyncio
async def test_list_knowledge_base_documents_returns_documents():
    knowledge_base_id = uuid4()
    document = SimpleNamespace(
        id=uuid4(),
        knowledge_base_id=knowledge_base_id,
        title="KB Document",
        content="content",
        source_type="manual",
        source_url=None,
        original_filename=None,
        mime_type=None,
        file_size=None,
        checksum=None,
        status="active",
        ingestion_status="ready",
    )

    class FakeDocumentRepository:
        async def find_by_knowledge_base_id(self, actual_id):
            assert actual_id == knowledge_base_id
            return [document]

    service = SimpleNamespace(get=AsyncMock(return_value=make_knowledge_base()))
    db = SimpleNamespace()

    from app.api.v1 import knowledge_bases as module

    original_repository = module.DocumentRepository
    module.DocumentRepository = lambda _: FakeDocumentRepository()
    try:
        response = await list_knowledge_base_documents(
            knowledge_base_id=knowledge_base_id,
            db=db,
            service=service,
            current_user=SimpleNamespace(),
        )
    finally:
        module.DocumentRepository = original_repository

    service.get.assert_awaited_once_with(knowledge_base_id)
    assert response["data"][0].knowledge_base_id == knowledge_base_id
