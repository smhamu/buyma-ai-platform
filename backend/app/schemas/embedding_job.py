from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmbeddingJobCreate(BaseModel):
    document_id: UUID
    chunk_id: UUID
    embedding_model_id: UUID


class EmbeddingJobGenerateRequest(BaseModel):
    embedding_model_id: UUID


class EmbeddingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_id: UUID
    embedding_model_id: UUID
    status: str
    retry_count: int
    error_message: str | None