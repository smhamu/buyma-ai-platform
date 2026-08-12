from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    is_active: bool
