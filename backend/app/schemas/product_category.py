from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brand import OnlinePurchasePolicy


class ProductCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category_code: str
    category_name: str
    is_active: bool


class BrandCategoryPolicyInput(BaseModel):
    category_id: UUID
    online_purchase_policy: OnlinePurchasePolicy
    research_enabled: bool = True
    policy_notes: str | None = Field(default=None, max_length=2000)
    checked_at: datetime | None = None


class BrandCategoryPolicyUpdate(BaseModel):
    online_purchase_policy: OnlinePurchasePolicy | None = None
    research_enabled: bool | None = None
    policy_notes: str | None = Field(default=None, max_length=2000)
    checked_at: datetime | None = None


class BrandCategoryPolicyResponse(BrandCategoryPolicyInput):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    brand_id: UUID
    category: ProductCategoryResponse
    created_at: datetime
    updated_at: datetime


class ResolvedPurchasePolicy(BaseModel):
    policy: OnlinePurchasePolicy
    research_enabled: bool
    source: str
