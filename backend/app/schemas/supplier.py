from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field
from app.schemas.brand import BrandSummary

CountryCode = Literal["FR", "IT", "DE", "ES", "NL", "BE", "AT", "IE", "PT"]
CurrencyCode = Literal["EUR", "JPY", "GBP", "CHF", "USD"]
VatPolicy = Literal["included", "excluded_for_export", "not_refunded", "unknown"]
BuymaAllowedStatus = Literal["unchecked", "allowed", "caution", "prohibited"]
SupplierResearchStatus = Literal["discovered", "reviewing", "approved", "rejected"]
SupplierType = Literal["authorized_retailer", "department_store", "boutique", "marketplace", "other", "unknown"]
IngestionSourceType = Literal["manual", "url_manual", "csv", "official_api", "structured_data", "html_parser", "disabled"]
TermsStatus = Literal["unchecked", "allowed", "restricted", "prohibited", "unknown"]
RobotsStatus = Literal["unchecked", "allowed", "restricted", "disallowed", "unknown"]


class SupplierBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    country_code: CountryCode
    website_url: AnyHttpUrl
    supplier_type: SupplierType = "unknown"
    default_currency: CurrencyCode = "EUR"
    ships_to_japan: bool = False
    vat_policy: VatPolicy = "unknown"
    vat_rate: Decimal | None = Field(default=None, ge=0, le=1)
    japan_shipping_cost: Decimal | None = Field(default=None, ge=0)
    buyma_allowed_status: BuymaAllowedStatus = "unchecked"
    buyma_status_checked_at: datetime | None = None
    research_status: SupplierResearchStatus = "discovered"
    notes: str | None = None
    is_active: bool = True
    ingestion_source_type: IngestionSourceType = "manual"
    automated_fetch_enabled: bool = False
    terms_status: TermsStatus = "unchecked"
    robots_status: RobotsStatus = "unchecked"
    terms_checked_at: datetime | None = None
    robots_checked_at: datetime | None = None
    official_api_available: bool = False
    research_policy_notes: str | None = None
    parser_key: str | None = Field(default=None, max_length=100)
    request_interval_seconds: int | None = Field(default=None, ge=1)
    last_fetch_at: datetime | None = None


class SupplierCreate(SupplierBase):
    brand_ids: list[UUID] = Field(default_factory=list)


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    country_code: CountryCode | None = None
    website_url: AnyHttpUrl | None = None
    supplier_type: SupplierType | None = None
    default_currency: CurrencyCode | None = None
    ships_to_japan: bool | None = None
    vat_policy: VatPolicy | None = None
    vat_rate: Decimal | None = Field(default=None, ge=0, le=1)
    japan_shipping_cost: Decimal | None = Field(default=None, ge=0)
    buyma_allowed_status: BuymaAllowedStatus | None = None
    buyma_status_checked_at: datetime | None = None
    research_status: SupplierResearchStatus | None = None
    notes: str | None = None
    is_active: bool | None = None
    brand_ids: list[UUID] | None = None
    ingestion_source_type: IngestionSourceType | None = None
    automated_fetch_enabled: bool | None = None
    terms_status: TermsStatus | None = None
    robots_status: RobotsStatus | None = None
    terms_checked_at: datetime | None = None
    robots_checked_at: datetime | None = None
    official_api_available: bool | None = None
    research_policy_notes: str | None = None
    parser_key: str | None = Field(default=None, max_length=100)
    request_interval_seconds: int | None = Field(default=None, ge=1)
    last_fetch_at: datetime | None = None


class SupplierResponse(SupplierBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_user_id: UUID
    created_at: datetime
    updated_at: datetime
    brands: list[BrandSummary] = Field(default_factory=list)
