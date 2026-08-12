from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RetrieverRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=4000,
        examples=["BUYMAの価格設定ルールを教えてください。"],
    )
    embedding_model_id: UUID
    knowledge_base_id: UUID | None = Field(
        default=None,
        description="Knowledge Base used as the retrieval scope.",
    )
    top_k: int = Field(default=5, ge=1, le=50, examples=[5])
    distance_threshold: float | None = Field(
        default=0.5,
        ge=0.0,
        le=2.0,
        examples=[0.5],
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query must not be blank.")
        return value


class RetrievedChunk(BaseModel):
    document_id: UUID
    chunk_id: UUID
    content: str
    distance: float


class RetrieverResponse(BaseModel):
    query: str
    context: str
    chunks: list[RetrievedChunk]
