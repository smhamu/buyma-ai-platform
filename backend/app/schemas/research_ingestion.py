from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from app.schemas.product_research import AvailabilityStatus, ProductPurchaseRestriction
from app.schemas.supplier import CurrencyCode

SourceType = Literal["manual", "url_manual", "csv", "official_api", "structured_data", "html_parser", "disabled"]
ProcessingStatus = Literal["pending", "fetched", "normalized", "matched", "candidate_created", "rejected", "failed"]


class UrlIngestionRequest(BaseModel):
    supplier_id: UUID
    url: AnyHttpUrl
    category_id: UUID | None = None
    purchase_restriction: ProductPurchaseRestriction | None = "unknown"


class ResearchSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_user_id: UUID
    supplier_id: UUID
    brand_id: UUID | None
    category_id: UUID | None
    source_type: SourceType
    source_url: str
    external_product_id: str | None
    fetched_at: datetime | None
    raw_title: str | None
    raw_brand: str | None
    raw_price: Decimal | None
    raw_currency: str | None
    raw_availability: str | None
    normalized_title: str | None
    normalized_price: Decimal | None
    normalized_currency: str | None
    normalized_availability: str | None
    purchase_restriction: ProductPurchaseRestriction | None
    processing_status: ProcessingStatus
    error_code: str | None
    error_message: str | None
    candidate_id: UUID | None
    created_at: datetime
    updated_at: datetime


class CandidateConversionRequest(BaseModel):
    exchange_rate: Decimal = Field(gt=0)
    buyma_price: Decimal = Field(gt=0)
    buyma_fee_rate: Decimal = Field(default=Decimal("0.077"), ge=0, le=1)
    estimated_import_cost: Decimal = Field(default=Decimal("0"), ge=0)
    estimated_other_cost: Decimal = Field(default=Decimal("0"), ge=0)
    japan_shipping_cost: Decimal | None = Field(default=None, ge=0)


class CsvRowResult(BaseModel):
    row: int
    status: Literal["success", "failed", "duplicate"]
    source_id: UUID | None = None
    message: str | None = None


class CsvImportResponse(BaseModel):
    success_count: int
    failed_count: int
    duplicate_count: int
    rows: list[CsvRowResult]
