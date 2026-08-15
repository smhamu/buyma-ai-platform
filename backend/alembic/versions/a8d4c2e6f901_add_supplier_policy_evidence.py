"""add supplier policy evidence

Revision ID: a8d4c2e6f901
Revises: f2c3d4e5a6b7
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a8d4c2e6f901"
down_revision: Union[str, Sequence[str], None] = "f2c3d4e5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_policy_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("source_title", sa.String(length=255), nullable=True),
        sa.Column("source_excerpt", sa.String(length=1000), nullable=True),
        sa.Column("evidence_notes", sa.Text(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checked_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["checked_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_supplier_policy_evidence_supplier_id", "supplier_policy_evidence", ["supplier_id"])
    op.create_index("ix_supplier_policy_evidence_supplier_type_checked", "supplier_policy_evidence", ["supplier_id", "evidence_type", "checked_at"])


def downgrade() -> None:
    op.drop_index("ix_supplier_policy_evidence_supplier_type_checked", table_name="supplier_policy_evidence")
    op.drop_index("ix_supplier_policy_evidence_supplier_id", table_name="supplier_policy_evidence")
    op.drop_table("supplier_policy_evidence")
