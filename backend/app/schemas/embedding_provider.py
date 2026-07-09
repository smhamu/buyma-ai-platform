from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmbeddingProviderCreate(BaseModel):
    provider_code: str
    provider_name: str
    endpoint: str | None = None
    is_active: bool = True


class EmbeddingProviderUpdate(BaseModel):
    provider_code: str | None = None
    provider_name: str | None = None
    endpoint: str | None = None
    is_active: bool | None = None


class EmbeddingProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_code: str
    provider_name: str
    endpoint: str | None
    is_active: bool