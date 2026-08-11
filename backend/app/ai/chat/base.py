from abc import ABC, abstractmethod


class ChatProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict[str, str]]) -> str:
        """LLMへmessagesを送信し、生成されたテキストを返す。"""
        raise NotImplementedError
