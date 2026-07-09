from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.embedding_provider_repository import EmbeddingProviderRepository
from app.schemas.embedding_provider import (
    EmbeddingProviderCreate,
    EmbeddingProviderResponse,
    EmbeddingProviderUpdate,
)
from app.services.embedding_provider_service import EmbeddingProviderService

router = APIRouter(prefix="/embedding-providers", tags=["Embedding Providers"])


def get_embedding_provider_service(
    db: AsyncSession = Depends(get_db),
) -> EmbeddingProviderService:
    repository = EmbeddingProviderRepository(db)
    return EmbeddingProviderService(repository)


@router.post("")
async def create_embedding_provider(
    payload: EmbeddingProviderCreate,
    service: EmbeddingProviderService = Depends(get_embedding_provider_service),
    current_user: User = Depends(require_admin),
):
    provider = await service.create(payload)

    return success_response(
        data=EmbeddingProviderResponse.model_validate(provider),
        message="Embedding provider created successfully.",
    )


@router.get("")
async def list_embedding_providers(
    service: EmbeddingProviderService = Depends(get_embedding_provider_service),
    current_user: User = Depends(get_current_user),
):
    providers = await service.list()

    return success_response(
        data=[EmbeddingProviderResponse.model_validate(provider) for provider in providers],
        message="Embedding providers fetched successfully.",
    )


@router.get("/{provider_id}")
async def get_embedding_provider(
    provider_id: UUID,
    service: EmbeddingProviderService = Depends(get_embedding_provider_service),
    current_user: User = Depends(get_current_user),
):
    provider = await service.get(provider_id)

    return success_response(
        data=EmbeddingProviderResponse.model_validate(provider),
        message="Embedding provider fetched successfully.",
    )


@router.put("/{provider_id}")
async def update_embedding_provider(
    provider_id: UUID,
    payload: EmbeddingProviderUpdate,
    service: EmbeddingProviderService = Depends(get_embedding_provider_service),
    current_user: User = Depends(require_admin),
):
    provider = await service.update(provider_id, payload)

    return success_response(
        data=EmbeddingProviderResponse.model_validate(provider),
        message="Embedding provider updated successfully.",
    )


@router.delete("/{provider_id}")
async def delete_embedding_provider(
    provider_id: UUID,
    service: EmbeddingProviderService = Depends(get_embedding_provider_service),
    current_user: User = Depends(require_admin),
):
    result = await service.delete(provider_id)

    return success_response(
        data=result,
        message="Embedding provider deleted successfully.",
    )