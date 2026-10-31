import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SupplierRakutenConfig(Base):
    __tablename__ = "supplier_rakuten_configs"
    __table_args__ = (
        UniqueConstraint("supplier_id", name="uq_supplier_rakuten_configs_supplier"),
        CheckConstraint(
            "approval_status IN ('not_applied','pending','approved','rejected','suspended')",
            name="ck_supplier_rakuten_approval_status",
        ),
        CheckConstraint("language IN ('en_US','fr_FR','de_DE','pt_BR')", name="ck_supplier_rakuten_language"),
        CheckConstraint("advertiser_mid > 0", name="ck_supplier_rakuten_advertiser_mid"),
        CheckConstraint("max_results BETWEEN 1 AND 100", name="ck_supplier_rakuten_max_results"),
        CheckConstraint("max_pages BETWEEN 1 AND 100", name="ck_supplier_rakuten_max_pages"),
        CheckConstraint(
            "sync_interval_minutes BETWEEN 15 AND 10080",
            name="ck_supplier_rakuten_sync_interval",
        ),
        CheckConstraint(
            "sync_enabled = false OR approval_status = 'approved'",
            name="ck_supplier_rakuten_sync_requires_approval",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    advertiser_mid: Mapped[int] = mapped_column(Integer, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    search_keyword: Mapped[str | None] = mapped_column(String(200), nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en_US")
    max_results: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1440)
    approved_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

