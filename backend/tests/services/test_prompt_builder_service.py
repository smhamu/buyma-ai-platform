from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.schemas.prompt_builder import PromptBuildRequest
from app.services.prompt_builder_service import PromptBuilderService


@pytest.mark.asyncio
async def test_prompt_builder_creates_system_and_user_messages():
    retriever_service = SimpleNamespace()

    async def retrieve(_):
        return SimpleNamespace(
            context="[Context 1]\nBUYMAの商品登録ルール",
            chunks=[],
        )

    retriever_service.retrieve = retrieve
    service = PromptBuilderService(retriever_service=retriever_service)

    result = await service.build(
        PromptBuildRequest(
            query="商品登録ルールを教えて",
            embedding_model_id=uuid4(),
            top_k=5,
        )
    )

    assert len(result.messages) == 2
    assert result.messages[0].role == "system"
    assert result.messages[1].role == "user"
    assert "Context" in result.messages[1].content
    assert "商品登録ルールを教えて" in result.messages[1].content
