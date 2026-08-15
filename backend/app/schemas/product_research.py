from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from app.schemas.supplier import CurrencyCode, VatPolicy

AvailabilityStatus = Literal["unknown", "in_stock", "out_of_stock", "preorder"]
CandidateResearchStatus = Literal[
    "discovered", "reviewing", "profitable", "unprofitable", "rejected", "ready_for_listing"
]


class ProductResearchInput(BaseModel):
    supplier_id: UUID
    brand_id: UUID
    supplier_product_url: AnyHttpUrl
    supplier_product_code: str | None = Field(default=None, max_length=255)
    product_name: str = Field(min_length=1, max_length=500)
    category: str | None = Field(default=None, max_length=255)
    category_id: UUID | None = None
    supplier_price: Decimal = Field(gt=0)
    supplier_currency: CurrencyCode
    vat_policy: VatPolicy
    vat_rate: Decimal | None = Field(default=None, ge=0, le=1)
    japan_shipping_cost: Decimal = Field(default=Decimal("0"), ge=0)
    exchange_rate: Decimal = Field(gt=0)
    estimated_import_cost: Decimal = Field(default=Decimal("0"), ge=0)
    estimated_other_cost: Decimal = Field(default=Decimal("0"), ge=0)
    buyma_price: Decimal = Field(gt=0)
    buyma_fee_rate: Decimal = Field(ge=0, le=1)
    availability_status: AvailabilityStatus = "unknown"
    research_status: CandidateResearchStatus = "discovered"
    checked_at: datetime | None = None
    online_purchase_available: bool = True
    is_active: bool = True


class ProductResearchCreate(ProductResearchInput):
    pass


class ProductResearchUpdate(BaseModel):
    brand_id: UUID | None = None
    supplier_product_url: AnyHttpUrl | None = None
    supplier_product_code: str | None = Field(default=None, max_length=255)
    product_name: str | None = Field(default=None, min_length=1, max_length=500)
    category: str | None = Field(default=None, max_length=255)
    category_id: UUID | None = None
    supplier_price: Decimal | None = Field(default=None, gt=0)
    supplier_currency: CurrencyCode | None = None
    vat_policy: VatPolicy | None = None
    vat_rate: Decimal | None = Field(default=None, ge=0, le=1)
    japan_shipping_cost: Decimal | None = Field(default=None, ge=0)
    exchange_rate: Decimal | None = Field(default=None, gt=0)
    estimated_import_cost: Decimal | None = Field(default=None, ge=0)
    estimated_other_cost: Decimal | None = Field(default=None, ge=0)
    buyma_price: Decimal | None = Field(default=None, gt=0)
    buyma_fee_rate: Decimal | None = Field(default=None, ge=0, le=1)
    availability_status: AvailabilityStatus | None = None
    research_status: CandidateResearchStatus | None = None
    checked_at: datetime | None = None
    is_active: bool | None = None


class PriceCalculationResponse(BaseModel):
    effective_supplier_price: Decimal
    export_price: Decimal | None
    supplier_cost_jpy: Decimal
    total_cost: Decimal
    buyma_fee: Decimal
    profit_amount: Decimal
    profit_rate: Decimal


class ProductResearchResponse(ProductResearchInput):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_user_id: UUID
    source_product_id: UUID | None = None
    export_price: Decimal | None
    supplier_cost_jpy: Decimal
    total_cost: Decimal
    buyma_fee: Decimal
    profit_amount: Decimal
    profit_rate: Decimal
    created_at: datetime
    updated_at: datetime
