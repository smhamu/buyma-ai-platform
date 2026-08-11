import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.schemas.prompt_builder import PromptBuildRequest
from app.services.prompt_builder_service import PromptBuilderService


class PromptBuilderServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_build_forwards_request_and_builds_chat_messages(self):
        model_id = uuid4()
        retriever_service = SimpleNamespace(
            retrieve=AsyncMock(
                return_value=SimpleNamespace(context="[Context 1]\nBUYMA rule")
            )
        )
        service = PromptBuilderService(retriever_service=retriever_service)
        payload = PromptBuildRequest(
            query="商品登録ルールを教えて",
            embedding_model_id=model_id,
            top_k=3,
        )

        result = await service.build(payload)

        retriever_payload = retriever_service.retrieve.await_args.args[0]
        self.assertEqual(retriever_payload.query, payload.query)
        self.assertEqual(retriever_payload.embedding_model_id, model_id)
        self.assertEqual(retriever_payload.top_k, 3)
        self.assertEqual(result.context, "[Context 1]\nBUYMA rule")
        self.assertEqual([message.role for message in result.messages], ["system", "user"])
        self.assertIn("[Context 1]\nBUYMA rule", result.messages[1].content)
        self.assertIn(payload.query, result.messages[1].content)

    async def test_build_uses_fallback_text_when_context_is_empty(self):
        retriever_service = SimpleNamespace(
            retrieve=AsyncMock(return_value=SimpleNamespace(context=""))
        )
        service = PromptBuilderService(retriever_service=retriever_service)

        result = await service.build(
            PromptBuildRequest(
                query="Unknown question",
                embedding_model_id=uuid4(),
            )
        )

        self.assertEqual(result.context, "")
        self.assertIn(
            "関連するContextは取得できませんでした。",
            result.messages[1].content,
        )


if __name__ == "__main__":
    unittest.main()
