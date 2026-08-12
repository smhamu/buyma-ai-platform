import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.schemas.prompt_builder import PromptMessage
from app.schemas.rag import RAGQueryRequest
from app.services.rag_service import RAGService


class RAGServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_query_builds_prompt_once_and_returns_answer_and_sources(self):
        model_id = uuid4()
        document_id = uuid4()
        chunk_id = uuid4()
        prompt_builder_service = SimpleNamespace(
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
        service = RAGService(prompt_builder_service=prompt_builder_service)
        payload = RAGQueryRequest(
            query="BUYMA rules",
            embedding_model_id=model_id,
            top_k=3,
        )

        with (
            patch(
                "app.services.rag_service.settings.openai_chat_model",
                "test-model",
            ),
            patch(
                "app.services.rag_service.ChatProviderFactory.create",
                return_value=chat_provider,
            ) as create_provider,
        ):
            result = await service.query(payload)

        prompt_builder_service.build.assert_awaited_once()
        prompt_payload = prompt_builder_service.build.await_args.args[0]
        self.assertEqual(prompt_payload.query, payload.query)
        self.assertEqual(prompt_payload.embedding_model_id, model_id)
        self.assertEqual(prompt_payload.top_k, 3)
        self.assertEqual(prompt_payload.distance_threshold, 0.5)
        create_provider.assert_called_once_with(
            provider_code="openai",
            model_name="test-model",
        )
        chat_provider.generate.assert_awaited_once_with(
            messages=[
                {"role": "system", "content": "Instructions"},
                {"role": "user", "content": "Question"},
            ]
        )
        self.assertEqual(result.answer, "Answer")
        self.assertEqual(result.context, "[Context 1]\nBUYMA rule")
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.sources[0].chunk_id, chunk_id)

    async def test_query_requires_chat_model_configuration(self):
        prompt_builder_service = SimpleNamespace(
            build=AsyncMock(
                return_value=SimpleNamespace(
                    context="[Context 1]\nRelevant information",
                    messages=[],
                    chunks=[SimpleNamespace()],
                )
            )
        )
        service = RAGService(prompt_builder_service=prompt_builder_service)

        with patch(
            "app.services.rag_service.settings.openai_chat_model",
            None,
        ):
            with self.assertRaisesRegex(ValueError, "OPENAI_CHAT_MODEL"):
                await service.query(
                    RAGQueryRequest(
                        query="Question",
                        embedding_model_id=uuid4(),
                    )
                )

        prompt_builder_service.build.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
