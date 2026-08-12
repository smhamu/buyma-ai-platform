from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import NotFoundException
from app.services.resource_authorization_service import ResourceAuthorizationService


@pytest.mark.asyncio
async def test_require_knowledge_base_access_returns_owned_kb_for_user():
    kb = SimpleNamespace(id=uuid4(), owner_user_id=uuid4())
    user = SimpleNamespace(id=kb.owner_user_id, role="user")
    service = ResourceAuthorizationService(
        knowledge_base_repository=SimpleNamespace(
            find_by_id_and_owner=lambda knowledge_base_id, owner_user_id: _awaitable(kb)
        ),
        document_repository=SimpleNamespace(),
    )

    result = await service.require_knowledge_base_access(kb.id, user)

    assert result is kb


@pytest.mark.asyncio
async def test_require_document_access_raises_for_unowned_document():
    document = SimpleNamespace(id=uuid4(), knowledge_base_id=uuid4())
    user = SimpleNamespace(id=uuid4(), role="user")
    service = ResourceAuthorizationService(
        knowledge_base_repository=SimpleNamespace(
            find_by_id_and_owner=lambda knowledge_base_id, owner_user_id: _awaitable(None)
        ),
        document_repository=SimpleNamespace(
            find_by_id=lambda document_id: _awaitable(document)
        ),
    )

    with pytest.raises(NotFoundException):
        await service.require_document_access(document.id, user)


async def _awaitable(value):
    return value
