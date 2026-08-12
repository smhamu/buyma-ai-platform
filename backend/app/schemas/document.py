from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentCreate(BaseModel):
    knowledge_base_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=200000)
    source_type: str = "manual"
    source_url: str | None = None
    status: str = "active"

    @field_validator("title", "content")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank.")
        return value


class DocumentUpdate(BaseModel):
    knowledge_base_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1, max_length=200000)
    source_type: str | None = None
    source_url: str | None = None
    status: str | None = None

    @field_validator("title", "content")
    @classmethod
    def validate_optional_non_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Field must not be blank.")
        return value


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
