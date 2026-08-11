from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from openai import OpenAIError

from app.ai.chat.openai_provider import OpenAIChatProvider
from app.ai.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.ai.openai_error_handler import handle_openai_error
from app.common.exceptions import AIProviderUnknownException


def test_unknown_openai_error_is_converted():
    with pytest.raises(AIProviderUnknownException) as exc_info:
        handle_openai_error(Exception("unexpected"))

    assert exc_info.value.status_code == 502
    assert exc_info.value.code == "AI_PROVIDER_ERROR"


@pytest.mark.asyncio
async def test_chat_provider_converts_openai_errors():
    provider = OpenAIChatProvider.__new__(OpenAIChatProvider)
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(side_effect=OpenAIError("failed"))
            )
        )
    )
    provider.model_name = "test-model"

    with patch(
        "app.ai.chat.openai_provider.handle_openai_error",
        side_effect=AIProviderUnknownException(),
    ) as handler:
        with pytest.raises(AIProviderUnknownException):
            await provider.generate([{"role": "user", "content": "Question"}])

    handler.assert_called_once()


@pytest.mark.asyncio
async def test_embedding_provider_converts_openai_errors():
    provider = OpenAIEmbeddingProvider.__new__(OpenAIEmbeddingProvider)
    provider.client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=AsyncMock(side_effect=OpenAIError("failed"))
        )
    )
    provider.model_name = "test-model"

    with patch(
        "app.ai.embeddings.openai_provider.handle_openai_error",
        side_effect=AIProviderUnknownException(),
    ) as handler:
        with pytest.raises(AIProviderUnknownException):
            await provider.generate_embedding("Question", 2)

    handler.assert_called_once()
