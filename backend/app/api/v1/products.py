from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import success_response
from app.core.database import get_db
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_service(
    db: AsyncSession = Depends(get_db),
) -> ProductService:
    repository = ProductRepository(db)
    return ProductService(repository)


@router.post("")
async def create_product(
    payload: ProductCreate,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
):
    product = await service.create(payload)
    return success_response(
        data=ProductResponse.model_validate(product),
        message="Product created successfully.",
    )

@router.get("")
async def list_products(
    service: ProductService = Depends(get_product_service),
):
    products = await service.list()
    return success_response(
        data=[ProductResponse.model_validate(product) for product in products],
        message="Products fetched successfully.",
    )


@router.get("/{product_id}")
async def get_product(
    product_id: UUID,
    service: ProductService = Depends(get_product_service),
):
    product = await service.get(product_id)
    return success_response(
        data=ProductResponse.model_validate(product),
        message="Product fetched successfully.",
    )


@router.put("/{product_id}")
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    service: ProductService = Depends(get_product_service),
):
    product = await service.update(product_id, payload)
    return success_response(
        data=ProductResponse.model_validate(product),
        message="Product updated successfully.",
    )


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    service: ProductService = Depends(get_product_service),
):
    result = await service.delete(product_id)
    return success_response(
        data=result,
        message="Product deleted successfully.",
    )

@router.get("")
async def list_products(
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
):
    products = await service.list()
    return success_response(
        data=[ProductResponse.model_validate(product) for product in products],
        message="Products fetched successfully.",
    )