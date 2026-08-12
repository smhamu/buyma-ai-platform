from uuid import UUID

from pydantic import BaseModel, Field


class VectorSearchRequest(BaseModel):
    query: str
    embedding_model_id: UUID
    knowledge_base_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=50)
    distance_threshold: float | None = Field(default=0.5, ge=0.0, le=2.0)


class VectorSearchResult(BaseModel):
    embedding_id: UUID
    document_id: UUID
    chunk_id: UUID
    content: str
    distance: float
