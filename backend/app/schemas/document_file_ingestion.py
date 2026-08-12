from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.document import DocumentResponse
from app.schemas.document_chunk import DocumentChunkResponse
from app.schemas.embedding_job import EmbeddingJobResponse


class DocumentFileIngestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filename: str
    file_size: int
    document: DocumentResponse
    chunks: list[DocumentChunkResponse]
    embedding_jobs: list[EmbeddingJobResponse]
    task_ids: list[str]
