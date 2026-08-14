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
from app.schemas.product_research import (
    PriceCalculationResponse, ProductResearchCreate, ProductResearchResponse, ProductResearchUpdate,
)
from app.services.product_research_service import ProductResearchService

router = APIRouter(prefix="/product-research-candidates", tags=["EU Product Research"])


def get_product_research_service(db: AsyncSession = Depends(get_db)) -> ProductResearchService:
    return ProductResearchService(ProductResearchRepository(db), SupplierRepository(db))


def _database_values(payload) -> dict:
    values = payload.model_dump(exclude_unset=True)
    if "supplier_product_url" in values and values["supplier_product_url"] is not None:
        values["supplier_product_url"] = str(values["supplier_product_url"])
    return values


@router.post("/calculate")
async def calculate_candidate(payload: ProductResearchCreate, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    supplier = await service.validate_supplier(payload.supplier_id, current_user.id, current_user.role == "admin")
    service.validate_listing_status(supplier, payload.research_status)
    result = service.calculate(payload.model_dump())
    return success_response(data=PriceCalculationResponse(**result.__dict__), message="Price calculated successfully.")


@router.post("")
async def create_candidate(payload: ProductResearchCreate, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    supplier = await service.validate_supplier(payload.supplier_id, current_user.id, current_user.role == "admin")
    service.validate_listing_status(supplier, payload.research_status)
    values = service.apply_calculation(_database_values(payload))
    values["owner_user_id"] = current_user.id
    candidate = await service.repository.create(values)
    return success_response(data=ProductResearchResponse.model_validate(candidate), message="Product research candidate created successfully.")


@router.get("")
async def list_candidates(
    brand: str | None = Query(default=None, max_length=255), supplier_id: UUID | None = None,
    country: str | None = Query(default=None, min_length=2, max_length=2), currency: str | None = None,
    research_status: str | None = None, availability_status: str | None = None,
    buyma_allowed_status: str | None = None, min_profit_amount: Decimal | None = None,
    min_profit_rate: Decimal | None = None, ships_to_japan: bool | None = None,
    service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user),
):
    candidates = await service.repository.find_all_filtered(
        owner_user_id=None if current_user.role == "admin" else current_user.id,
        brand=brand, supplier_id=supplier_id, country=country, currency=currency,
        research_status=research_status, availability_status=availability_status,
        buyma_allowed_status=buyma_allowed_status, min_profit_amount=min_profit_amount,
        min_profit_rate=min_profit_rate, ships_to_japan=ships_to_japan,
    )
    return success_response(data=[ProductResearchResponse.model_validate(item) for item in candidates], message="Product research candidates fetched successfully.")


@router.get("/{candidate_id}")
async def get_candidate(candidate_id: UUID, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    candidate = await service.require_access(candidate_id, current_user.id, current_user.role == "admin")
    return success_response(data=ProductResearchResponse.model_validate(candidate), message="Product research candidate fetched successfully.")


@router.put("/{candidate_id}")
async def update_candidate(candidate_id: UUID, payload: ProductResearchUpdate, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    candidate = await service.require_access(candidate_id, current_user.id, current_user.role == "admin")
    supplier = await service.validate_supplier(candidate.supplier_id, current_user.id, current_user.role == "admin")
    updates = _database_values(payload)
    target_status = updates.get("research_status", candidate.research_status)
    service.validate_listing_status(supplier, target_status)
    merged = {field: updates.get(field, getattr(candidate, field)) for field in service.CALCULATION_FIELDS}
    updates.update({key: value for key, value in service.apply_calculation(merged).items() if key not in service.CALCULATION_FIELDS})
    candidate = await service.repository.update(candidate, updates)
    return success_response(data=ProductResearchResponse.model_validate(candidate), message="Product research candidate updated successfully.")


@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: UUID, service: ProductResearchService = Depends(get_product_research_service), current_user: User = Depends(get_current_user)):
    candidate = await service.require_access(candidate_id, current_user.id, current_user.role == "admin")
    await service.repository.delete(candidate)
    return success_response(data={"deleted": True}, message="Product research candidate deleted successfully.")
