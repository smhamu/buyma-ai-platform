import unittest
from unittest.mock import AsyncMock, patch

from app.api.v1.chat_test import chat_test


class ChatTestEndpointTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_chat_test_generates_answer(self):
        provider = AsyncMock()
        provider.generate.return_value = "こんにちは。"

        with (
            patch(
                "app.api.v1.chat_test.settings.openai_chat_model",
                "test-model",
            ),
            patch(
                "app.api.v1.chat_test.ChatProviderFactory.create",
                return_value=provider,
            ) as create,
        ):
            response = await chat_test(current_user=object())

        create.assert_called_once_with(
            provider_code="openai",
            model_name="test-model",
        )
        provider.generate.assert_awaited_once()
        self.assertEqual(response["data"]["answer"], "こんにちは。")

    async def test_chat_test_requires_model_configuration(self):
        with patch(
            "app.api.v1.chat_test.settings.openai_chat_model",
            None,
        ):
            with self.assertRaisesRegex(ValueError, "OPENAI_CHAT_MODEL"):
                await chat_test(current_user=object())


if __name__ == "__main__":
    unittest.main()
