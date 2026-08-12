from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.document import DocumentResponse
from app.schemas.document_chunk import DocumentChunkResponse
from app.schemas.embedding_job import EmbeddingJobResponse


class DocumentIngestionRequest(BaseModel):
    knowledge_base_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=200000)
    source_type: str = "manual"
    source_url: str | None = None
    original_filename: str | None = Field(default=None, max_length=255)
    mime_type: str | None = None
    file_size: int | None = None
    checksum: str | None = None
    version: int = 1
    previous_document_id: UUID | None = None
    version_group_id: UUID | None = None
    is_latest: bool = True
    status: str = "active"
    embedding_model_id: UUID
    chunk_size: int = Field(default=500, ge=100, le=5000)
    auto_enqueue: bool = True

    @field_validator("title", "content")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank.")
        return value


class DocumentIngestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document: DocumentResponse
    chunks: list[DocumentChunkResponse]
    embedding_jobs: list[EmbeddingJobResponse]
    task_ids: list[str]
