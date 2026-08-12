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
        version=1,
        previous_document_id=None,
        version_group_id=uuid4(),
        is_latest=True,
        status="active",
        ingestion_status="ready",
    )

    service = SimpleNamespace(
        list_documents=AsyncMock(
            return_value={
                "items": [document],
                "total": 1,
                "total_pages": 1,
            }
        )
    )

    response = await list_knowledge_base_documents(
        knowledge_base_id=knowledge_base_id,
        page=1,
        page_size=20,
        q=None,
        status=None,
        ingestion_status=None,
        is_latest=True,
        source_type=None,
        sort_by="created_at",
        sort_order="desc",
        service=service,
        current_user=SimpleNamespace(),
    )

    service.list_documents.assert_awaited_once_with(
        knowledge_base_id=knowledge_base_id,
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
    assert response["data"]["items"][0]["knowledge_base_id"] == knowledge_base_id
    assert response["data"]["page"] == 1
    assert response["data"]["page_size"] == 20
    assert response["data"]["total"] == 1
    assert response["data"]["total_pages"] == 1
    assert response["data"]["sort_by"] == "created_at"
    assert response["data"]["sort_order"] == "desc"
