import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


supplier_brands = Table(
    "supplier_brands",
    Base.metadata,
    Column("supplier_id", UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), primary_key=True),
    Column("brand_id", UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), primary_key=True),
)


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    luxury_tier: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    official_site_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    online_purchase_policy: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    purchase_restriction_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_research_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    suppliers = relationship("Supplier", secondary=supplier_brands, back_populates="brands")
