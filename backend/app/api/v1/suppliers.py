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
from datetime import datetime
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.services.supplier_service import SupplierService
from app.repositories.supplier_policy_evidence_repository import SupplierPolicyEvidenceRepository
from app.schemas.supplier_policy_evidence import (
    EvidenceResult,
    EvidenceType,
    PolicyEvidenceSummaryItem,
    SupplierPolicyEvidenceCreate,
    SupplierPolicyEvidenceEnvelope,
    SupplierPolicyEvidenceListEnvelope,
    SupplierPolicyEvidenceResponse,
    SupplierPolicyEvidenceSummaryEnvelope,
)
from app.services.supplier_policy_evidence_service import SupplierPolicyEvidenceService

router = APIRouter(prefix="/suppliers", tags=["EU Suppliers"])


def get_supplier_service(db: AsyncSession = Depends(get_db)) -> SupplierService:
    return SupplierService(SupplierRepository(db), BrandRepository(db))


def get_policy_evidence_service(db: AsyncSession = Depends(get_db)) -> SupplierPolicyEvidenceService:
    supplier_service = SupplierService(SupplierRepository(db), BrandRepository(db))
    return SupplierPolicyEvidenceService(SupplierPolicyEvidenceRepository(db), supplier_service)


@router.post(
    "/{supplier_id}/policy-evidence",
    response_model=SupplierPolicyEvidenceEnvelope,
    description="Append evidence for a supplier policy review. Evidence is immutable and does not change the current Supplier policy.",
)
async def create_policy_evidence(
    supplier_id: UUID,
    payload: SupplierPolicyEvidenceCreate,
    service: SupplierPolicyEvidenceService = Depends(get_policy_evidence_service),
    current_user: User = Depends(get_current_user),
):
    evidence = await service.create(supplier_id, payload, current_user)
    return success_response(
        data=SupplierPolicyEvidenceResponse.model_validate(evidence),
        message="Supplier policy evidence recorded. Current policy was not changed.",
    )


@router.get(
    "/{supplier_id}/policy-evidence/latest",
    response_model=SupplierPolicyEvidenceSummaryEnvelope,
    description="Return each tracked policy's current value and latest evidence without loading the full history.",
)
async def latest_policy_evidence(
    supplier_id: UUID,
    max_age_days: int | None = Query(default=None, ge=1, le=3650),
    service: SupplierPolicyEvidenceService = Depends(get_policy_evidence_service),
    current_user: User = Depends(get_current_user),
):
    summary = await service.summary(supplier_id, current_user, max_age_days)
    data = {key: PolicyEvidenceSummaryItem.model_validate(value) for key, value in summary.items()}
    return success_response(data=data, message="Supplier policy evidence summary fetched successfully.")


@router.get(
    "/{supplier_id}/policy-evidence",
    response_model=SupplierPolicyEvidenceListEnvelope,
    description="List immutable policy evidence history. Access follows Supplier ownership; inaccessible Suppliers return 404.",
)
async def list_policy_evidence(
    supplier_id: UUID,
    evidence_type: EvidenceType | None = None,
    result: EvidenceResult | None = None,
    checked_from: datetime | None = None,
    checked_to: datetime | None = None,
    q: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: Literal["checked_at", "created_at", "evidence_type"] = "checked_at",
    sort_order: Literal["asc", "desc"] = "desc",
    service: SupplierPolicyEvidenceService = Depends(get_policy_evidence_service),
    current_user: User = Depends(get_current_user),
):
    await service.supplier_service.require_access(supplier_id, current_user.id, current_user.role == "admin")
    result_page = await service.repository.list_filtered(
        supplier_id=supplier_id, evidence_type=evidence_type, result=result,
        checked_from=checked_from, checked_to=checked_to, q=q, page=page,
        page_size=page_size, sort_by=sort_by, sort_order=sort_order,
    )
    data = PaginatedResponse[SupplierPolicyEvidenceResponse](
        items=[SupplierPolicyEvidenceResponse.model_validate(item) for item in result_page["items"]],
        page=page, page_size=page_size, total=result_page["total"],
        total_pages=(result_page["total"] + page_size - 1) // page_size,
    )
    return success_response(data=data, message="Supplier policy evidence history fetched successfully.")


@router.get(
    "/{supplier_id}/policy-evidence/{evidence_id}",
    response_model=SupplierPolicyEvidenceEnvelope,
    description="Get one immutable evidence record. Access follows Supplier ownership.",
)
async def get_policy_evidence(
    supplier_id: UUID,
    evidence_id: UUID,
    service: SupplierPolicyEvidenceService = Depends(get_policy_evidence_service),
    current_user: User = Depends(get_current_user),
):
    evidence = await service.require_access(supplier_id, evidence_id, current_user)
    return success_response(
        data=SupplierPolicyEvidenceResponse.model_validate(evidence),
        message="Supplier policy evidence fetched successfully.",
    )


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
