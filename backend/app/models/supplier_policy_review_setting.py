import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SupplierPolicyReviewSetting(Base):
    __tablename__ = "supplier_policy_review_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    terms_max_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    robots_max_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vat_max_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shipping_max_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    official_api_max_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    buyma_max_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_evidence_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
