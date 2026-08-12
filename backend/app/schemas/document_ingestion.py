from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.document import DocumentResponse
from app.schemas.document_chunk import DocumentChunkResponse
from app.schemas.embedding_job import EmbeddingJobResponse


class DocumentIngestionRequest(BaseModel):
    knowledge_base_id: UUID | None = None
    title: str
    content: str
    source_type: str = "manual"
    source_url: str | None = None
    original_filename: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    checksum: str | None = None
    status: str = "active"
    embedding_model_id: UUID
    chunk_size: int = Field(default=500, ge=100, le=5000)
    auto_enqueue: bool = True


class DocumentIngestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document: DocumentResponse
    chunks: list[DocumentChunkResponse]
    embedding_jobs: list[EmbeddingJobResponse]
    task_ids: list[str]
