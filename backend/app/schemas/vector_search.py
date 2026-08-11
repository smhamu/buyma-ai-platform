from uuid import UUID

from pydantic import BaseModel


class VectorSearchRequest(BaseModel):
    query: str
    embedding_model_id: UUID
    top_k: int = 5


class VectorSearchResult(BaseModel):
    embedding_id: UUID
    document_id: UUID
    chunk_id: UUID
    content: str
    distance: float