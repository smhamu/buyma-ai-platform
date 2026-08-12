from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RAGQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    embedding_model_id: UUID
    knowledge_base_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=50)
    distance_threshold: float | None = Field(default=0.5, ge=0.0, le=2.0)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query must not be blank.")
        return value


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
