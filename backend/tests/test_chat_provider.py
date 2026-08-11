import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.ai.chat.factory import ChatProviderFactory
from app.ai.chat.openai_provider import OpenAIChatProvider


class OpenAIChatProviderTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_generate_sends_messages_and_returns_content(self):
        create = AsyncMock(
            return_value=SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="Generated answer")
                    )
                ]
            )
        )
        provider = OpenAIChatProvider.__new__(OpenAIChatProvider)
        provider.client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        provider.model_name = "test-model"
        messages = [
            {"role": "system", "content": "System instructions"},
            {"role": "user", "content": "Question"},
        ]

        result = await provider.generate(messages)

        self.assertEqual(result, "Generated answer")
        create.assert_awaited_once_with(
            model="test-model",
            messages=[
                {"role": "system", "content": "System instructions"},
                {"role": "user", "content": "Question"},
            ],
        )

    async def test_generate_rejects_empty_text_content(self):
        provider = OpenAIChatProvider.__new__(OpenAIChatProvider)
        provider.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=AsyncMock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content=None)
                                )
                            ]
                        )
                    )
                )
            )
        )
        provider.model_name = "test-model"

        with self.assertRaisesRegex(ValueError, "empty response"):
            await provider.generate(
                [{"role": "user", "content": "Question"}]
            )

    def test_init_requires_openai_api_key(self):
        with patch("app.ai.chat.openai_provider.settings.openai_api_key", None):
            with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
                OpenAIChatProvider(model_name="test-model")


class ChatProviderFactoryTestCase(unittest.TestCase):
    @patch("app.ai.chat.factory.OpenAIChatProvider")
    def test_create_returns_openai_provider(self, provider_class):
        provider = ChatProviderFactory.create("openai", "test-model")

        provider_class.assert_called_once_with(model_name="test-model")
        self.assertIs(provider, provider_class.return_value)

    def test_create_rejects_unsupported_provider(self):
        with self.assertRaisesRegex(ValueError, "Unsupported chat provider"):
            ChatProviderFactory.create("unknown", "test-model")


if __name__ == "__main__":
    unittest.main()
