from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.schemas.pagination import PaginatedResponse

EvidenceType = Literal[
    "terms", "robots", "vat", "shipping", "official_api", "buyma",
    "ingestion", "resale_restriction", "other",
]
EvidenceResult = Literal[
    "allowed", "restricted", "prohibited", "disallowed", "supported", "unsupported",
    "confirmed", "unconfirmed", "unknown", "unchecked", "caution", "included",
    "excluded_for_export", "not_refunded", "manual", "url_manual", "csv",
    "official_api", "structured_data", "html_parser", "disabled",
]


class SupplierPolicyEvidenceCreate(BaseModel):
    evidence_type: EvidenceType
    result: EvidenceResult
    source_url: str | None = Field(default=None, max_length=2048)
    source_title: str | None = Field(default=None, max_length=255)
    source_excerpt: str | None = Field(default=None, max_length=1000)
    evidence_notes: str = Field(min_length=1, max_length=4000)
    checked_at: datetime

    @model_validator(mode="after")
    def validate_result_for_type(self):
        allowed = {
            "terms": {"allowed", "restricted", "prohibited", "unknown"},
            "robots": {"allowed", "restricted", "disallowed", "unknown"},
            "vat": {"included", "excluded_for_export", "not_refunded", "unknown"},
            "shipping": {"supported", "unsupported", "confirmed", "unconfirmed", "unknown"},
            "official_api": {"supported", "unsupported", "confirmed", "unconfirmed", "unknown"},
            "buyma": {"unchecked", "allowed", "caution", "prohibited", "unknown"},
            "ingestion": {"manual", "url_manual", "csv", "official_api", "structured_data", "html_parser", "disabled", "supported", "unsupported", "unknown"},
            "resale_restriction": {"allowed", "restricted", "prohibited", "confirmed", "unconfirmed", "unknown"},
            "other": set(EvidenceResult.__args__),
        }
        if self.result not in allowed[self.evidence_type]:
            raise ValueError(f"Result '{self.result}' is not valid for evidence type '{self.evidence_type}'.")
        return self

    @field_validator("checked_at")
    @classmethod
    def reject_naive_or_far_future_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("checked_at must include a timezone.")
        if value > datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=5):
            raise ValueError("checked_at cannot be more than five minutes in the future.")
        return value


class SupplierPolicyEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    supplier_id: UUID
    owner_user_id: UUID
    evidence_type: EvidenceType
    result: EvidenceResult
    source_url: str | None
    source_title: str | None
    source_excerpt: str | None
    evidence_notes: str
    checked_at: datetime
    checked_by_user_id: UUID
    checked_by_username: str
    policy_snapshot: dict
    created_at: datetime
    updated_at: datetime


class PolicyEvidenceSummaryItem(BaseModel):
    current: str | bool
    latest_evidence: str | None
    evidence_id: UUID | None
    checked_at: datetime | None
    age_days: int | None
    is_stale: bool | None
    consistent: bool | None


class SupplierPolicyEvidenceEnvelope(BaseModel):
    success: bool
    message: str
    data: SupplierPolicyEvidenceResponse


class SupplierPolicyEvidenceListEnvelope(BaseModel):
    success: bool
    message: str
    data: PaginatedResponse[SupplierPolicyEvidenceResponse]


class SupplierPolicyEvidenceSummaryEnvelope(BaseModel):
    success: bool
    message: str
    data: dict[str, PolicyEvidenceSummaryItem]
