from openai import AsyncOpenAI, OpenAIError

from app.ai.chat.base import ChatProvider
from app.ai.openai_error_handler import handle_openai_error
from app.core.config import settings


class OpenAIChatProvider(ChatProvider):
    def __init__(self, model_name: str):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model_name = model_name

    async def generate(self, messages: list[dict[str, str]]) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
        except OpenAIError as exc:
            handle_openai_error(exc)

        content = response.choices[0].message.content

        if content is None:
            raise ValueError("OpenAI returned an empty response.")

        return content
