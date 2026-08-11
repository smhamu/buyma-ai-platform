from app.ai.chat.base import ChatProvider
from app.ai.chat.openai_provider import OpenAIChatProvider


class ChatProviderFactory:
    @staticmethod
    def create(
        provider_code: str,
        model_name: str,
    ) -> ChatProvider:
        if provider_code == "openai":
            return OpenAIChatProvider(model_name=model_name)

        raise ValueError(f"Unsupported chat provider: {provider_code}")
