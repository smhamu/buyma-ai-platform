from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    title: str
    content: str
    source_type: str = "manual"
    source_url: str | None = None
    status: str = "active"


class DocumentUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    status: str | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    source_type: str
    source_url: str | None
    status: str