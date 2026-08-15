import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    website_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    supplier_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown", index=True)
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    ships_to_japan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vat_policy: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    vat_rate: Mapped[float | None] = mapped_column(Numeric(7, 6), nullable=True)
    japan_shipping_cost: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    buyma_allowed_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unchecked", index=True
    )
    buyma_status_checked_at = mapped_column(DateTime(timezone=True), nullable=True)
    research_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="discovered", index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ingestion_source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    automated_fetch_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    terms_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unchecked")
    robots_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unchecked")
    terms_checked_at = mapped_column(DateTime(timezone=True), nullable=True)
    robots_checked_at = mapped_column(DateTime(timezone=True), nullable=True)
    official_api_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    research_policy_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    parser_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    request_interval_seconds: Mapped[int | None] = mapped_column(nullable=True)
    last_fetch_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    brands = relationship("Brand", secondary="supplier_brands", back_populates="suppliers", lazy="selectin")
    policy_evidence = relationship(
        "SupplierPolicyEvidence", cascade="all, delete-orphan", passive_deletes=True
    )
