from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1.rag import rag_query
from app.api.v1.retriever import retrieve
from app.api.v1.vector_search import vector_search
from app.common.exceptions import AppException
from app.schemas.rag import RAGQueryRequest
from app.schemas.retriever import RetrieverRequest
from app.schemas.vector_search import VectorSearchRequest


@pytest.mark.asyncio
async def test_vector_search_requires_knowledge_base_for_non_admin():
    with pytest.raises(AppException) as exc_info:
        await vector_search(
            payload=VectorSearchRequest(
                query="hello",
                embedding_model_id=uuid4(),
                knowledge_base_id=None,
            ),
            service=SimpleNamespace(search=None),
            authz=SimpleNamespace(),
            current_user=SimpleNamespace(role="user"),
        )

    assert exc_info.value.code == "KNOWLEDGE_BASE_REQUIRED"


@pytest.mark.asyncio
async def test_retriever_requires_kb_access_when_specified():
    authz = SimpleNamespace(require_knowledge_base_access=_async_noop)
    service = SimpleNamespace(
        retrieve=_async_return(SimpleNamespace(model_dump=lambda: {"chunks": [], "prompt_context": ""}))
    )
    current_user = SimpleNamespace(role="user")
    knowledge_base_id = uuid4()

    await retrieve(
        payload=RetrieverRequest(
            query="hello",
            embedding_model_id=uuid4(),
            knowledge_base_id=knowledge_base_id,
        ),
        service=service,
        authz=authz,
        current_user=current_user,
    )


@pytest.mark.asyncio
async def test_rag_requires_knowledge_base_for_non_admin():
    with pytest.raises(AppException) as exc_info:
        await rag_query(
            payload=RAGQueryRequest(
                query="secret",
                embedding_model_id=uuid4(),
                knowledge_base_id=None,
            ),
            service=SimpleNamespace(query=None),
            authz=SimpleNamespace(),
            current_user=SimpleNamespace(role="user"),
        )

    assert exc_info.value.code == "KNOWLEDGE_BASE_REQUIRED"


async def _async_noop(*args, **kwargs):
    return None


def _async_return(value):
    async def _inner(*args, **kwargs):
        return value

    return _inner
