from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

ReviewEvidenceType = Literal["terms", "robots", "vat", "shipping", "official_api", "buyma"]
ReviewStatus = Literal["up_to_date", "review_due", "inconsistent", "no_evidence"]


class SupplierPolicyReviewSettingsUpdate(BaseModel):
    terms_max_age_days: int | None = Field(default=180, ge=1, le=3650)
    robots_max_age_days: int | None = Field(default=180, ge=1, le=3650)
    vat_max_age_days: int | None = Field(default=180, ge=1, le=3650)
    shipping_max_age_days: int | None = Field(default=180, ge=1, le=3650)
    official_api_max_age_days: int | None = Field(default=365, ge=1, le=3650)
    buyma_max_age_days: int | None = Field(default=90, ge=1, le=3650)
    required_evidence_types: list[ReviewEvidenceType] = Field(
        default_factory=lambda: ["terms", "robots", "vat", "shipping", "buyma"]
    )

    @field_validator("required_evidence_types")
    @classmethod
    def unique_types(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("required_evidence_types must not contain duplicates.")
        return value


class SupplierPolicyReviewSettingsResponse(SupplierPolicyReviewSettingsUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID | None = None
    user_id: UUID


class PolicyTypeReview(BaseModel):
    current: str
    latest_evidence: str | None
    checked_at: datetime | None
    age_days: int | None
    max_age_days: int | None
    consistent: bool | None
    is_stale: bool | None
    review_status: ReviewStatus


class SupplierPolicyReviewItem(BaseModel):
    supplier_id: UUID
    supplier_name: str
    country_code: str
    supplier_type: str
    brand_names: list[str]
    updated_at: datetime
    overall_status: ReviewStatus
    priority: Literal["critical", "high", "medium", "normal"]
    issue_types: list[ReviewEvidenceType]
    oldest_evidence_at: datetime | None
    types: dict[ReviewEvidenceType, PolicyTypeReview]


class SupplierPolicyReviewPage(BaseModel):
    items: list[SupplierPolicyReviewItem]
    page: int
    page_size: int
    total: int
    total_pages: int
    summary: dict[str, int]


class SupplierPolicyReviewTransitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    supplier_id: UUID
    state_version: int
    from_status: ReviewStatus | None
    to_status: ReviewStatus
    changed_evidence_types: list[ReviewEvidenceType]
    reason_summary: str
    occurred_at: datetime
    created_at: datetime


class NotificationOutboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    event_type: Literal["supplier_policy_review_changed"]
    resource_type: Literal["supplier"]
    resource_id: UUID
    payload: dict
    dedupe_key: str
    status: Literal["pending", "processing", "delivered", "failed", "cancelled"]
    available_at: datetime
    processed_at: datetime | None
    attempt_count: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime
