from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmbeddingModelCreate(BaseModel):
    provider_id: UUID
    model_name: str
    model_version: str = "default"
    dimension: int
    distance_metric: str = "cosine"
    is_active: bool = True


class EmbeddingModelUpdate(BaseModel):
    provider_id: UUID | None = None
    model_name: str | None = None
    model_version: str | None = None
    dimension: int | None = None
    distance_metric: str | None = None
    is_active: bool | None = None


class EmbeddingModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    model_name: str
    model_version: str
    dimension: int
    distance_metric: str
    is_active: bool