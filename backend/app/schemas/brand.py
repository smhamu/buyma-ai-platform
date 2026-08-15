from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

LuxuryTier = Literal["ultra_luxury", "luxury", "premium"]
OnlinePurchasePolicy = Literal["normal", "limited", "category_limited", "boutique_only", "research_only", "unknown"]


class BrandBase(BaseModel):
    brand_code: str = Field(pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=100)
    brand_name: str = Field(min_length=1, max_length=255)
    luxury_tier: LuxuryTier
    official_site_url: AnyHttpUrl | None = None
    online_purchase_policy: OnlinePurchasePolicy = "unknown"
    purchase_restriction_notes: str | None = None
    is_research_enabled: bool = True
    is_active: bool = True

    @field_validator("brand_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.lower()


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    brand_name: str | None = Field(default=None, min_length=1, max_length=255)
    luxury_tier: LuxuryTier | None = None
    official_site_url: AnyHttpUrl | None = None
    online_purchase_policy: OnlinePurchasePolicy | None = None
    purchase_restriction_notes: str | None = None
    is_research_enabled: bool | None = None
    is_active: bool | None = None


class BrandResponse(BrandBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class BrandSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    brand_code: str
    brand_name: str
