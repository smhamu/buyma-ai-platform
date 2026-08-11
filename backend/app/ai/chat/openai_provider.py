from openai import AsyncOpenAI

from app.ai.chat.base import ChatProvider
from app.core.config import settings


class OpenAIChatProvider(ChatProvider):
    def __init__(self, model_name: str):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model_name = model_name

    async def generate(self, messages: list[dict[str, str]]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        content = response.choices[0].message.content

        if content is None:
            raise ValueError("OpenAI returned an empty response.")

        return content
