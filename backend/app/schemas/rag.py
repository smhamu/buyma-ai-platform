from uuid import UUID

from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    query: str
    embedding_model_id: UUID
    top_k: int = 5
    distance_threshold: float | None = 0.4


class RAGSource(BaseModel):
    document_id: UUID
    chunk_id: UUID
    content: str
    distance: float


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    context: str
    sources: list[RAGSource]
