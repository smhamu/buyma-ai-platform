from uuid import UUID

from pydantic import BaseModel


class RetrieverRequest(BaseModel):
    query: str
    embedding_model_id: UUID
    knowledge_base_id: UUID | None = None
    top_k: int = 5
    distance_threshold: float | None = 0.5


class RetrievedChunk(BaseModel):
    document_id: UUID
    chunk_id: UUID
    content: str
    distance: float


class RetrieverResponse(BaseModel):
    query: str
    context: str
    chunks: list[RetrievedChunk]
