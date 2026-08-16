"""add user notification channels and deliveries

Revision ID: e2b8c6d0a345
Revises: d1a7f5b9c234
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e2b8c6d0a345"
down_revision = "d1a7f5b9c234"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_notification_outbox_status", "notification_outbox", type_="check")
    op.create_check_constraint(
        "ck_notification_outbox_status", "notification_outbox",
        "status IN ('pending','processing','expanded','delivered','failed','cancelled')",
    )
    op.create_table(
        "notification_channel_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_type", sa.String(32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("destination_label", sa.String(100), nullable=False),
        sa.Column("subscribed_event_types", sa.JSON(), nullable=False),
        sa.Column("secret_reference", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("channel_type IN ('slack','email','line')", name="ck_notification_channel_type"),
        sa.UniqueConstraint("user_id", "channel_type", name="uq_notification_channel_user_type"),
    )
    op.create_index("ix_notification_channel_settings_user_id", "notification_channel_settings", ["user_id"])
    op.create_table(
        "notification_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("outbox_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notification_outbox.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_setting_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notification_channel_settings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_type", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("provider_status_code", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("channel_type IN ('slack','email','line')", name="ck_notification_delivery_channel_type"),
        sa.CheckConstraint("status IN ('pending','processing','delivered','failed','cancelled')", name="ck_notification_delivery_status"),
        sa.UniqueConstraint("outbox_id", "channel_setting_id", name="uq_notification_delivery_outbox_channel"),
    )
    for column in ("outbox_id", "channel_setting_id", "user_id", "event_type", "resource_id", "status", "available_at"):
        op.create_index(f"ix_notification_deliveries_{column}", "notification_deliveries", [column])
    op.create_index("ix_notification_delivery_claim", "notification_deliveries", ["status", "available_at"])
    op.create_index("ix_notification_delivery_lease", "notification_deliveries", ["status", "lease_expires_at"])


def downgrade() -> None:
    op.drop_table("notification_deliveries")
    op.drop_table("notification_channel_settings")
    op.drop_constraint("ck_notification_outbox_status", "notification_outbox", type_="check")
    op.execute("UPDATE notification_outbox SET status = 'delivered' WHERE status = 'expanded'")
    op.create_check_constraint(
        "ck_notification_outbox_status", "notification_outbox",
        "status IN ('pending','processing','delivered','failed','cancelled')",
    )
