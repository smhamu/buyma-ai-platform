from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.schemas.embedding_model import (
    EmbeddingModelCreate,
    EmbeddingModelResponse,
    EmbeddingModelUpdate,
)
from app.services.embedding_model_service import EmbeddingModelService

router = APIRouter(prefix="/embedding-models", tags=["Embedding Models"])


def get_embedding_model_service(
    db: AsyncSession = Depends(get_db),
) -> EmbeddingModelService:
    repository = EmbeddingModelRepository(db)
    return EmbeddingModelService(repository)


@router.post("")
async def create_embedding_model(
    payload: EmbeddingModelCreate,
    service: EmbeddingModelService = Depends(get_embedding_model_service),
    current_user: User = Depends(require_admin),
):
    model = await service.create(payload)

    return success_response(
        data=EmbeddingModelResponse.model_validate(model),
        message="Embedding model created successfully.",
    )


@router.get("")
async def list_embedding_models(
    service: EmbeddingModelService = Depends(get_embedding_model_service),
    current_user: User = Depends(get_current_user),
):
    models = await service.list()

    return success_response(
        data=[EmbeddingModelResponse.model_validate(model) for model in models],
        message="Embedding models fetched successfully.",
    )


@router.get("/{model_id}")
async def get_embedding_model(
    model_id: UUID,
    service: EmbeddingModelService = Depends(get_embedding_model_service),
    current_user: User = Depends(get_current_user),
):
    model = await service.get(model_id)

    return success_response(
        data=EmbeddingModelResponse.model_validate(model),
        message="Embedding model fetched successfully.",
    )


@router.put("/{model_id}")
async def update_embedding_model(
    model_id: UUID,
    payload: EmbeddingModelUpdate,
    service: EmbeddingModelService = Depends(get_embedding_model_service),
    current_user: User = Depends(require_admin),
):
    model = await service.update(model_id, payload)

    return success_response(
        data=EmbeddingModelResponse.model_validate(model),
        message="Embedding model updated successfully.",
    )


@router.delete("/{model_id}")
async def delete_embedding_model(
    model_id: UUID,
    service: EmbeddingModelService = Depends(get_embedding_model_service),
    current_user: User = Depends(require_admin),
):
    result = await service.delete(model_id)

    return success_response(
        data=result,
        message="Embedding model deleted successfully.",
    )