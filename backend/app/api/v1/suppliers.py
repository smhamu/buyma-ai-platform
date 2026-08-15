from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.brand_repository import BrandRepository
from app.schemas.pagination import PaginatedResponse
from typing import Literal
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["EU Suppliers"])


def get_supplier_service(db: AsyncSession = Depends(get_db)) -> SupplierService:
    return SupplierService(SupplierRepository(db), BrandRepository(db))


@router.post("")
async def create_supplier(payload: SupplierCreate, service: SupplierService = Depends(get_supplier_service), current_user: User = Depends(get_current_user)):
    values = payload.model_dump()
    brand_ids = values.pop("brand_ids")
    values["website_url"] = str(values["website_url"])
    values["owner_user_id"] = current_user.id
    supplier = await service.repository.create(values)
    await service.set_brands(supplier, brand_ids)
    return success_response(data=SupplierResponse.model_validate(supplier), message="Supplier created successfully.")


@router.get("")
async def list_suppliers(
    country: str | None = Query(default=None, min_length=2, max_length=2),
    supplier_type: str | None = None,
    ships_to_japan: bool | None = None,
    buyma_allowed_status: str | None = None,
    research_status: str | None = None,
    is_active: bool | None = True,
    page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
    sort_by: Literal["name", "country_code", "created_at", "updated_at"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    service: SupplierService = Depends(get_supplier_service),
    current_user: User = Depends(get_current_user),
):
    result = await service.repository.find_all_filtered(
        owner_user_id=None if current_user.role == "admin" else current_user.id,
        country=country, supplier_type=supplier_type, ships_to_japan=ships_to_japan,
        buyma_allowed_status=buyma_allowed_status, research_status=research_status,
        is_active=is_active, page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order,
    )
    data = PaginatedResponse[SupplierResponse](items=[SupplierResponse.model_validate(item) for item in result["items"]], page=page, page_size=page_size, total=result["total"], total_pages=(result["total"] + page_size - 1) // page_size)
    return success_response(data=data, message="Suppliers fetched successfully.")


@router.get("/{supplier_id}")
async def get_supplier(supplier_id: UUID, service: SupplierService = Depends(get_supplier_service), current_user: User = Depends(get_current_user)):
    supplier = await service.require_access(supplier_id, current_user.id, current_user.role == "admin")
    return success_response(data=SupplierResponse.model_validate(supplier), message="Supplier fetched successfully.")


@router.put("/{supplier_id}")
async def update_supplier(supplier_id: UUID, payload: SupplierUpdate, service: SupplierService = Depends(get_supplier_service), current_user: User = Depends(get_current_user)):
    supplier = await service.require_access(supplier_id, current_user.id, current_user.role == "admin")
    values = payload.model_dump(exclude_unset=True)
    brand_ids = values.pop("brand_ids", None)
    if "website_url" in values and values["website_url"] is not None:
        values["website_url"] = str(values["website_url"])
    supplier = await service.repository.update(supplier, values)
    if brand_ids is not None:
        await service.set_brands(supplier, brand_ids)
    return success_response(data=SupplierResponse.model_validate(supplier), message="Supplier updated successfully.")


@router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: UUID, service: SupplierService = Depends(get_supplier_service), current_user: User = Depends(get_current_user)):
    supplier = await service.require_access(supplier_id, current_user.id, current_user.role == "admin")
    await service.repository.delete(supplier)
    return success_response(data={"deleted": True}, message="Supplier deleted successfully.")
