"""add policy review state transition and outbox

Revision ID: c0f6e4a8b123
Revises: b9e5d3f7a012
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c0f6e4a8b123"
down_revision: Union[str, Sequence[str], None] = "b9e5d3f7a012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_policy_review_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_status", sa.String(32), nullable=False),
        sa.Column("issue_types", sa.JSON(), nullable=False),
        sa.Column("type_statuses", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("supplier_id"),
    )
    op.create_index("ix_supplier_policy_review_states_supplier_id", "supplier_policy_review_states", ["supplier_id"], unique=True)
    op.create_index("ix_supplier_policy_review_states_owner_user_id", "supplier_policy_review_states", ["owner_user_id"])
    op.create_table(
        "supplier_policy_review_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("changed_evidence_types", sa.JSON(), nullable=False),
        sa.Column("reason_summary", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_id", "state_version", name="uq_supplier_policy_review_transition_version"),
    )
    op.create_index("ix_supplier_policy_review_transitions_supplier_id", "supplier_policy_review_transitions", ["supplier_id"])
    op.create_index("ix_supplier_policy_review_transitions_owner_user_id", "supplier_policy_review_transitions", ["owner_user_id"])
    op.create_index("ix_supplier_policy_review_transitions_occurred_at", "supplier_policy_review_transitions", ["occurred_at"])
    op.create_table(
        "notification_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("dedupe_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transition_id"], ["supplier_policy_review_transitions.id"], ondelete="CASCADE"),
        sa.CheckConstraint("event_type = 'supplier_policy_review_changed'", name="ck_notification_outbox_event_type"),
        sa.CheckConstraint("resource_type = 'supplier'", name="ck_notification_outbox_resource_type"),
        sa.CheckConstraint("status IN ('pending','processing','delivered','failed','cancelled')", name="ck_notification_outbox_status"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("dedupe_key"), sa.UniqueConstraint("transition_id"),
    )
    op.create_index("ix_notification_outbox_owner_user_id", "notification_outbox", ["owner_user_id"])
    op.create_index("ix_notification_outbox_resource_id", "notification_outbox", ["resource_id"])
    op.create_index("ix_notification_outbox_status", "notification_outbox", ["status"])
    op.create_index("ix_notification_outbox_available_at", "notification_outbox", ["available_at"])


def downgrade() -> None:
    op.drop_table("notification_outbox")
    op.drop_table("supplier_policy_review_transitions")
    op.drop_table("supplier_policy_review_states")
