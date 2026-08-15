import uuid

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ResearchSourceProduct(Base):
    __tablename__ = "research_source_products"
    __table_args__ = (
        UniqueConstraint("supplier_id", "external_product_id", name="uq_source_supplier_external"),
        UniqueConstraint("supplier_id", "normalized_source_url", name="uq_source_supplier_url"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    normalized_source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    external_product_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fetched_at = mapped_column(DateTime(timezone=True), nullable=True)
    raw_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_price: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    raw_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    raw_availability: Mapped[str | None] = mapped_column(String(32), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    normalized_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    normalized_price: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    normalized_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    normalized_availability: Mapped[str | None] = mapped_column(String(32), nullable=True)
    purchase_restriction: Mapped[str | None] = mapped_column(String(32), nullable=True, default="unknown", index=True)
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
