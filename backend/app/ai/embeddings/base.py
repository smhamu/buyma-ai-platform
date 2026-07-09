from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    async def generate_embedding(
        self,
        text: str,
        dimension: int,
    ) -> list[float]:
        pass