"""add supplier policy review settings

Revision ID: b9e5d3f7a012
Revises: a8d4c2e6f901
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b9e5d3f7a012"
down_revision: Union[str, Sequence[str], None] = "a8d4c2e6f901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_policy_review_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("terms_max_age_days", sa.Integer(), nullable=True),
        sa.Column("robots_max_age_days", sa.Integer(), nullable=True),
        sa.Column("vat_max_age_days", sa.Integer(), nullable=True),
        sa.Column("shipping_max_age_days", sa.Integer(), nullable=True),
        sa.Column("official_api_max_age_days", sa.Integer(), nullable=True),
        sa.Column("buyma_max_age_days", sa.Integer(), nullable=True),
        sa.Column("required_evidence_types", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_supplier_policy_review_settings_user_id", "supplier_policy_review_settings", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_supplier_policy_review_settings_user_id", table_name="supplier_policy_review_settings")
    op.drop_table("supplier_policy_review_settings")
