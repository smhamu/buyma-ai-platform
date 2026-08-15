from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.brand_repository import BrandRepository
from app.schemas.brand import BrandCreate, BrandResponse, BrandUpdate
from app.schemas.common import SuccessResponse
from app.schemas.pagination import PaginatedResponse
from app.services.brand_service import BrandService

router = APIRouter(prefix="/brands", tags=["Brand Master"])


def get_brand_service(db: AsyncSession = Depends(get_db)) -> BrandService:
    return BrandService(BrandRepository(db))


@router.post("", response_model=SuccessResponse[BrandResponse])
async def create_brand(payload: BrandCreate, service: BrandService = Depends(get_brand_service), _: User = Depends(require_admin)):
    values = payload.model_dump()
    if values["official_site_url"] is not None:
        values["official_site_url"] = str(values["official_site_url"])
    brand = await service.create(values)
    return success_response(data=BrandResponse.model_validate(brand), message="Brand created successfully.")


@router.get("", response_model=SuccessResponse[PaginatedResponse[BrandResponse]])
async def list_brands(
    q: str | None = Query(default=None, max_length=255), luxury_tier: str | None = None,
    online_purchase_policy: str | None = None, is_research_enabled: bool | None = None,
    is_active: bool | None = True, page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: Literal["brand_name", "luxury_tier", "created_at", "updated_at"] = "brand_name",
    sort_order: Literal["asc", "desc"] = "asc",
    service: BrandService = Depends(get_brand_service), _: User = Depends(get_current_user),
):
    result = await service.repository.list_paginated(q=q, luxury_tier=luxury_tier,
        online_purchase_policy=online_purchase_policy, is_research_enabled=is_research_enabled,
        is_active=is_active, page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    data = PaginatedResponse[BrandResponse](items=[BrandResponse.model_validate(x) for x in result["items"]], page=page, page_size=page_size, total=result["total"], total_pages=(result["total"] + page_size - 1) // page_size)
    return success_response(data=data, message="Brands fetched successfully.")


@router.get("/{brand_id}", response_model=SuccessResponse[BrandResponse])
async def get_brand(brand_id: UUID, service: BrandService = Depends(get_brand_service), _: User = Depends(get_current_user)):
    return success_response(data=BrandResponse.model_validate(await service.get(brand_id)), message="Brand fetched successfully.")


@router.put("/{brand_id}", response_model=SuccessResponse[BrandResponse])
async def update_brand(brand_id: UUID, payload: BrandUpdate, service: BrandService = Depends(get_brand_service), _: User = Depends(require_admin)):
    brand = await service.get(brand_id)
    values = payload.model_dump(exclude_unset=True)
    if values.get("official_site_url") is not None:
        values["official_site_url"] = str(values["official_site_url"])
    brand = await service.repository.update(brand, values)
    return success_response(data=BrandResponse.model_validate(brand), message="Brand updated successfully.")


@router.delete("/{brand_id}")
async def delete_brand(brand_id: UUID, service: BrandService = Depends(get_brand_service), _: User = Depends(require_admin)):
    await service.delete(brand_id)
    return success_response(data={"deleted": True}, message="Brand deleted successfully.")
