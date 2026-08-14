import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProductResearchCandidate(Base):
    __tablename__ = "product_research_candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_product_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    supplier_product_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supplier_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    supplier_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    vat_policy: Mapped[str] = mapped_column(String(32), nullable=False)
    vat_rate: Mapped[float | None] = mapped_column(Numeric(7, 6), nullable=True)
    export_price: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    japan_shipping_cost: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    exchange_rate: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    supplier_cost_jpy: Mapped[float] = mapped_column(Numeric(18, 0), nullable=False)
    estimated_import_cost: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    estimated_other_cost: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 0), nullable=False)
    buyma_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    buyma_fee_rate: Mapped[float] = mapped_column(Numeric(7, 6), nullable=False)
    buyma_fee: Mapped[float] = mapped_column(Numeric(18, 0), nullable=False)
    profit_amount: Mapped[float] = mapped_column(Numeric(18, 0), nullable=False, index=True)
    profit_rate: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False, index=True)
    availability_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unknown", index=True
    )
    research_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="discovered", index=True
    )
    checked_at = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
