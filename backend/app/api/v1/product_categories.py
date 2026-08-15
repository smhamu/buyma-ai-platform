from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.common.exceptions import NotFoundException
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.brand_repository import BrandRepository
from app.repositories.product_category_repository import BrandCategoryPolicyRepository, ProductCategoryRepository
from app.schemas.product_category import BrandCategoryPolicyInput, BrandCategoryPolicyResponse, BrandCategoryPolicyUpdate, ProductCategoryResponse, ResolvedPurchasePolicy
from app.services.brand_category_policy_service import BrandCategoryPolicyService

router = APIRouter(tags=["Brand Category Policy"])


def service(db: AsyncSession = Depends(get_db)):
    return BrandCategoryPolicyService(BrandRepository(db), ProductCategoryRepository(db), BrandCategoryPolicyRepository(db))


@router.get("/product-categories")
async def categories(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    items = await ProductCategoryRepository(db).find_active()
    return success_response(data=[ProductCategoryResponse.model_validate(x) for x in items], message="Product categories fetched successfully.")


@router.get("/brands/{brand_id}/category-policies")
async def list_policies(brand_id: UUID, svc=Depends(service), _: User = Depends(get_current_user)):
    if await svc.brands.find_by_id(brand_id) is None:
        raise NotFoundException("Brand")
    items = await svc.policies.list_for_brand(brand_id)
    return success_response(data=[BrandCategoryPolicyResponse.model_validate(x) for x in items], message="Category policies fetched successfully.")


@router.get("/brands/{brand_id}/resolved-purchase-policy")
async def resolved_policy(brand_id: UUID, category_id: UUID | None = None, svc=Depends(service), _: User = Depends(get_current_user)):
    policy, enabled, source = await svc.resolve(brand_id, category_id)
    return success_response(data=ResolvedPurchasePolicy(policy=policy, research_enabled=enabled, source=source), message="Purchase policy resolved successfully.")


@router.post("/brands/{brand_id}/category-policies")
async def create_policy(brand_id: UUID, payload: BrandCategoryPolicyInput, svc=Depends(service), _: User = Depends(require_admin)):
    item = await svc.create(brand_id, payload.model_dump())
    return success_response(data=BrandCategoryPolicyResponse.model_validate(item), message="Category policy created successfully.")


@router.put("/brands/{brand_id}/category-policies/{policy_id}")
async def update_policy(brand_id: UUID, policy_id: UUID, payload: BrandCategoryPolicyUpdate, svc=Depends(service), _: User = Depends(require_admin)):
    item = await svc.policies.find_for_brand(policy_id, brand_id)
    if item is None:
        raise NotFoundException("Brand category policy")
    item = await svc.policies.update(item, payload.model_dump(exclude_unset=True))
    return success_response(data=BrandCategoryPolicyResponse.model_validate(item), message="Category policy updated successfully.")


@router.delete("/brands/{brand_id}/category-policies/{policy_id}")
async def delete_policy(brand_id: UUID, policy_id: UUID, svc=Depends(service), _: User = Depends(require_admin)):
    item = await svc.policies.find_for_brand(policy_id, brand_id)
    if item is None:
        raise NotFoundException("Brand category policy")
    await svc.policies.delete(item)
    return success_response(data={"deleted": True}, message="Category policy deleted successfully.")
