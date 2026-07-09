from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmbeddingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_id: UUID
    embedding_model_id: UUID
    embedding_job_id: UUID
    dimension: int
    status: str
    metadata_text: str | None