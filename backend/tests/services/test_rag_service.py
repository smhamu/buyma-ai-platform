from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.prompt_builder import PromptMessage
from app.schemas.rag import RAGQueryRequest
from app.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_query_connects_prompt_builder_to_chat_provider_and_returns_sources():
    document_id = uuid4()
    chunk_id = uuid4()
    prompt_builder = SimpleNamespace(
        build=AsyncMock(
            return_value=SimpleNamespace(
                context="[Context 1]\nBUYMA rule",
                messages=[
                    PromptMessage(role="system", content="Instructions"),
                    PromptMessage(role="user", content="Question"),
                ],
                chunks=[
                    SimpleNamespace(
                        document_id=document_id,
                        chunk_id=chunk_id,
                        content="BUYMA rule",
                        distance=0.1,
                    )
                ],
            )
        )
    )
    chat_provider = SimpleNamespace(generate=AsyncMock(return_value="Answer"))
    service = RAGService(prompt_builder_service=prompt_builder)

    with (
        patch("app.services.rag_service.settings.openai_chat_model", "test-model"),
        patch(
            "app.services.rag_service.ChatProviderFactory.create",
            return_value=chat_provider,
        ),
    ):
        result = await service.query(
            RAGQueryRequest(
                query="Question",
                embedding_model_id=uuid4(),
                top_k=5,
            )
        )

    prompt_builder.build.assert_awaited_once()
    chat_provider.generate.assert_awaited_once()
    assert result.answer == "Answer"
    assert result.context == "[Context 1]\nBUYMA rule"
    assert len(result.sources) == 1
    assert result.sources[0].document_id == document_id
    assert result.sources[0].chunk_id == chunk_id


@pytest.mark.asyncio
async def test_query_returns_fallback_without_creating_chat_provider_when_empty():
    prompt_builder = SimpleNamespace(
        build=AsyncMock(
            return_value=SimpleNamespace(
                context="",
                messages=[
                    PromptMessage(role="system", content="Instructions"),
                    PromptMessage(role="user", content="No context"),
                ],
                chunks=[],
            )
        )
    )
    service = RAGService(prompt_builder_service=prompt_builder)

    with patch(
        "app.services.rag_service.ChatProviderFactory.create"
    ) as create_provider:
        result = await service.query(
            RAGQueryRequest(
                query="Unknown",
                embedding_model_id=uuid4(),
                distance_threshold=0.1,
            )
        )

    create_provider.assert_not_called()
    assert result.context == ""
    assert result.sources == []
    assert "関連する情報が見つかりませんでした" in result.answer
