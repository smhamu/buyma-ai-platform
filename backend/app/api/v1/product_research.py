from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.product_research_repository import ProductResearchRepository
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.brand_repository import BrandRepository
from app.schemas.pagination import PaginatedResponse
from typing import Literal
from app.schemas.product_research import (
    PriceCalculationResponse, ProductResearchCreate, ProductResearchResponse, ProductResearchUpdate,
)
from app.services.product_research_service import ProductResearchService

router = APIRouter(prefix="/product-research-candidates", tags=["EU Product Research"])


def get_product_research_service(db: AsyncSession = Depends(get_db)) -> ProductResearchService:
    return ProductResearchService(ProductResearchRepository(db), SupplierRepository(db), BrandRepository(db))


def _database_values(payload) -> dict:
    values = payload.model_dump(exclude_unset=True)
    if "supplier_product_url" in values and values["supplier_product_url"] is not None:
        values["supplier_product_url"] = str(values["supplier_product_url"])
    return values


@router.post("/calculate")
async def calculate_candidate(payload: ProductResearchCreate, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    supplier = await service.validate_supplier(payload.supplier_id, current_user.id, current_user.role == "admin")
    brand = await service.validate_brand(payload.brand_id)
    service.validate_listing_status(supplier, brand, payload.research_status, online_purchase_available=payload.online_purchase_available, availability_status=payload.availability_status)
    result = service.calculate(payload.model_dump())
    return success_response(data=PriceCalculationResponse(**result.__dict__), message="Price calculated successfully.")


@router.post("")
async def create_candidate(payload: ProductResearchCreate, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    supplier = await service.validate_supplier(payload.supplier_id, current_user.id, current_user.role == "admin")
    brand = await service.validate_brand(payload.brand_id)
    service.validate_listing_status(supplier, brand, payload.research_status, online_purchase_available=payload.online_purchase_available, availability_status=payload.availability_status)
    values = service.apply_calculation(_database_values(payload))
    values["owner_user_id"] = current_user.id
    candidate = await service.repository.create(values)
    return success_response(data=ProductResearchResponse.model_validate(candidate), message="Product research candidate created successfully.")


@router.get("")
async def list_candidates(
    q: str | None = Query(default=None, max_length=500), brand: str | None = Query(default=None, max_length=255),
    brand_id: UUID | None = None, brand_code: str | None = Query(default=None, max_length=100), supplier_id: UUID | None = None,
    country: str | None = Query(default=None, min_length=2, max_length=2), currency: str | None = None,
    research_status: str | None = None, availability_status: str | None = None,
    buyma_allowed_status: str | None = None, min_profit_amount: Decimal | None = None,
    min_profit_rate: Decimal | None = None, ships_to_japan: bool | None = None,
    page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
    sort_by: Literal["product_name", "supplier_price", "buyma_price", "profit_amount", "profit_rate", "checked_at", "created_at"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user),
):
    result = await service.repository.find_all_filtered(
        owner_user_id=None if current_user.role == "admin" else current_user.id,
        q=q, brand=brand, brand_id=brand_id, brand_code=brand_code, supplier_id=supplier_id, country=country, currency=currency,
        research_status=research_status, availability_status=availability_status,
        buyma_allowed_status=buyma_allowed_status, min_profit_amount=min_profit_amount,
        min_profit_rate=min_profit_rate, ships_to_japan=ships_to_japan,
        page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order,
    )
    data = PaginatedResponse[ProductResearchResponse](items=[ProductResearchResponse.model_validate(item) for item in result["items"]], page=page, page_size=page_size, total=result["total"], total_pages=(result["total"] + page_size - 1) // page_size)
    return success_response(data=data, message="Product research candidates fetched successfully.")


@router.get("/{candidate_id}")
async def get_candidate(candidate_id: UUID, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    candidate = await service.require_access(candidate_id, current_user.id, current_user.role == "admin")
    return success_response(data=ProductResearchResponse.model_validate(candidate), message="Product research candidate fetched successfully.")


@router.put("/{candidate_id}")
async def update_candidate(candidate_id: UUID, payload: ProductResearchUpdate, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    candidate = await service.require_access(candidate_id, current_user.id, current_user.role == "admin")
    supplier = await service.validate_supplier(candidate.supplier_id, current_user.id, current_user.role == "admin")
    target_brand_id = payload.brand_id or candidate.brand_id
    brand = await service.validate_brand(target_brand_id)
    updates = _database_values(payload)
    target_status = updates.get("research_status", candidate.research_status)
    service.validate_listing_status(supplier, brand, target_status, online_purchase_available=updates.get("online_purchase_available", candidate.online_purchase_available), availability_status=updates.get("availability_status", candidate.availability_status))
    merged = {field: updates.get(field, getattr(candidate, field)) for field in service.CALCULATION_FIELDS}
    updates.update({key: value for key, value in service.apply_calculation(merged).items() if key not in service.CALCULATION_FIELDS})
    candidate = await service.repository.update(candidate, updates)
    return success_response(data=ProductResearchResponse.model_validate(candidate), message="Product research candidate updated successfully.")


@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: UUID, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    candidate = await service.require_access(candidate_id, current_user.id, current_user.role == "admin")
    await service.repository.delete(candidate)
    return success_response(data={"deleted": True}, message="Product research candidate deleted successfully.")
