import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NotificationChannelSetting(Base):
    __tablename__ = "notification_channel_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "channel_type", name="uq_notification_channel_user_type"),
        CheckConstraint("channel_type IN ('slack','email','line')", name="ck_notification_channel_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    destination_label: Mapped[str] = mapped_column(String(100), nullable=False, default="Slack")
    subscribed_event_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    secret_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
