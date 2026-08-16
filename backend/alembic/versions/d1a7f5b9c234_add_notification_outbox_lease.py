"""add notification outbox processing lease

Revision ID: d1a7f5b9c234
Revises: c0f6e4a8b123
"""

from alembic import op
import sqlalchemy as sa

revision = "d1a7f5b9c234"
down_revision = "c0f6e4a8b123"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notification_outbox", sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notification_outbox", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_notification_outbox_claim", "notification_outbox", ["status", "available_at"]
    )
    op.create_index(
        "ix_notification_outbox_lease", "notification_outbox", ["status", "lease_expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_notification_outbox_lease", table_name="notification_outbox")
    op.drop_index("ix_notification_outbox_claim", table_name="notification_outbox")
    op.drop_column("notification_outbox", "lease_expires_at")
    op.drop_column("notification_outbox", "processing_started_at")
