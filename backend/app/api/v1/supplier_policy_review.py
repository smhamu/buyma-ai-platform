from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.brand_repository import BrandRepository
from app.repositories.supplier_policy_evidence_repository import SupplierPolicyEvidenceRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier_policy_review import (
    ReviewEvidenceType, ReviewStatus, SupplierPolicyReviewItem, SupplierPolicyReviewPage,
    SupplierPolicyReviewTransitionResponse,
    SupplierPolicyReviewSettingsResponse, SupplierPolicyReviewSettingsUpdate,
)
from app.services.supplier_policy_evidence_service import SupplierPolicyEvidenceService
from app.services.supplier_policy_review_service import SupplierPolicyReviewService
from app.services.supplier_service import SupplierService
from app.models.supplier_policy_review_transition import SupplierPolicyReviewTransition
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/supplier-policy-review", tags=["Supplier Policy Review"])


def get_service(db: AsyncSession = Depends(get_db)):
    suppliers = SupplierService(SupplierRepository(db), BrandRepository(db))
    evidence = SupplierPolicyEvidenceService(SupplierPolicyEvidenceRepository(db), suppliers)
    return SupplierPolicyReviewService(db, evidence)


@router.get("/settings")
async def get_settings(service=Depends(get_service), current_user: User = Depends(get_current_user)):
    row = await service.settings(current_user.id)
    data = SupplierPolicyReviewSettingsResponse.model_validate(row, from_attributes=True)
    return success_response(data=data, message="Supplier policy review settings fetched successfully.")


@router.put("/settings")
async def put_settings(payload: SupplierPolicyReviewSettingsUpdate, service=Depends(get_service), current_user: User = Depends(get_current_user)):
    row = await service.update_settings(current_user.id, payload)
    return success_response(data=SupplierPolicyReviewSettingsResponse.model_validate(row), message="Supplier policy review settings updated successfully.")


@router.get("")
async def review_queue(
    overall_status: ReviewStatus | None = None, evidence_type: ReviewEvidenceType | None = None,
    country: str | None = Query(default=None, min_length=2, max_length=2), supplier_type: str | None = None,
    brand: str | None = None, q: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
    sort: Literal["review_priority", "oldest_evidence", "supplier_name", "updated_at"] = "review_priority",
    service=Depends(get_service), current_user: User = Depends(get_current_user),
):
    result = await service.queue(current_user, overall_status=overall_status, evidence_type=evidence_type, country=country, supplier_type=supplier_type, brand=brand, q=q, page=page, page_size=page_size, sort=sort)
    data = SupplierPolicyReviewPage.model_validate(result)
    return success_response(data=data, message="Supplier policy review queue fetched successfully.")


@router.get("/{supplier_id}")
async def review_detail(supplier_id: UUID, service=Depends(get_service), current_user: User = Depends(get_current_user)):
    supplier = await service.evidence_service.supplier_service.require_access(supplier_id, current_user.id, current_user.role == "admin")
    settings = await service.settings(current_user.id)
    data = SupplierPolicyReviewItem.model_validate(await service.evaluate(supplier, settings))
    return success_response(data=data, message="Supplier policy review fetched successfully.")


@router.get("/{supplier_id}/transitions")
async def review_transitions(
    supplier_id: UUID, page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100), service=Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    await service.evidence_service.supplier_service.require_access(supplier_id, current_user.id, current_user.role == "admin")
    filters = [SupplierPolicyReviewTransition.supplier_id == supplier_id]
    total = int((await service.db.scalar(select(func.count(SupplierPolicyReviewTransition.id)).where(*filters))) or 0)
    rows = await service.db.execute(
        select(SupplierPolicyReviewTransition).where(*filters)
        .order_by(desc(SupplierPolicyReviewTransition.occurred_at), desc(SupplierPolicyReviewTransition.id))
        .offset((page - 1) * page_size).limit(page_size)
    )
    data = PaginatedResponse[SupplierPolicyReviewTransitionResponse](
        items=[SupplierPolicyReviewTransitionResponse.model_validate(item) for item in rows.scalars()],
        page=page, page_size=page_size, total=total, total_pages=(total + page_size - 1) // page_size,
    )
    return success_response(data=data, message="Supplier policy review transitions fetched successfully.")
