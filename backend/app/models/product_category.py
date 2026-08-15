import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    category_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BrandCategoryPolicy(Base):
    __tablename__ = "brand_category_policies"
    __table_args__ = (UniqueConstraint("brand_id", "category_id", name="uq_brand_category_policy"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    online_purchase_policy: Mapped[str] = mapped_column(String(32), nullable=False)
    research_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    policy_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("ProductCategory", lazy="selectin")
