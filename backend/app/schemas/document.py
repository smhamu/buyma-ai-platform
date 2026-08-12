from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    knowledge_base_id: UUID | None = None
    title: str
    content: str
    source_type: str = "manual"
    source_url: str | None = None
    status: str = "active"


class DocumentUpdate(BaseModel):
    knowledge_base_id: UUID | None = None
    title: str | None = None
    content: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    status: str | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    knowledge_base_id: UUID | None
    title: str
    content: str
    source_type: str
    source_url: str | None
    original_filename: str | None
    mime_type: str | None
    file_size: int | None
    checksum: str | None
    version: int
    previous_document_id: UUID | None
    version_group_id: UUID
    is_latest: bool
    status: str
    ingestion_status: str
