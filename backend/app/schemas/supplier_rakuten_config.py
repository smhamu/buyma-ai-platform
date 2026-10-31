from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RakutenApprovalStatus = Literal["not_applied", "pending", "approved", "rejected", "suspended"]
RakutenLanguage = Literal["en_US", "fr_FR", "de_DE", "pt_BR"]


class SupplierRakutenConfigUpdate(BaseModel):
    advertiser_mid: int = Field(gt=0)
    approval_status: RakutenApprovalStatus = "pending"
    sync_enabled: bool = False
    search_keyword: str | None = Field(default=None, max_length=200)
    language: RakutenLanguage = "en_US"
    max_results: int = Field(default=100, ge=1, le=100)
    max_pages: int = Field(default=10, ge=1, le=100)
    sync_interval_minutes: int = Field(default=1440, ge=15, le=10080)

    @field_validator("search_keyword")
    @classmethod
    def validate_search_keyword(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if any(char in value for char in "&=?{}\\()[];~|$!><*%"):
            raise ValueError("The Rakuten search keyword contains unsupported characters.")
        return value

    @model_validator(mode="after")
    def sync_requires_approval(self):
        if self.sync_enabled and self.approval_status != "approved":
            raise ValueError("Synchronization cannot be enabled before advertiser approval.")
        return self


class SupplierRakutenConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    configured: bool
    id: UUID | None = None
    supplier_id: UUID
    advertiser_mid: int | None = None
    approval_status: RakutenApprovalStatus = "not_applied"
    sync_enabled: bool = False
    search_keyword: str | None = None
    language: RakutenLanguage = "en_US"
    max_results: int = 100
    max_pages: int = 10
    sync_interval_minutes: int = 1440
    approved_at: datetime | None = None
    can_sync: bool
    blocked_reasons: list[str]
    created_at: datetime | None = None
    updated_at: datetime | None = None
