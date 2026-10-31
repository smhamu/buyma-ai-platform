"""add supplier rakuten configs

Revision ID: a4c8e2f1b907
Revises: e2b8c6d0a345
"""
from alembic import op
import sqlalchemy as sa

revision = "a4c8e2f1b907"
down_revision = "e2b8c6d0a345"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_rakuten_configs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("supplier_id", sa.UUID(), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("advertiser_mid", sa.Integer(), nullable=False),
        sa.Column("approval_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("sync_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("search_keyword", sa.String(200)),
        sa.Column("language", sa.String(10), nullable=False, server_default="en_US"),
        sa.Column("max_results", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("max_pages", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("sync_interval_minutes", sa.Integer(), nullable=False, server_default="1440"),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("supplier_id", name="uq_supplier_rakuten_configs_supplier"),
        sa.CheckConstraint("approval_status IN ('not_applied','pending','approved','rejected','suspended')", name="ck_supplier_rakuten_approval_status"),
        sa.CheckConstraint("language IN ('en_US','fr_FR','de_DE','pt_BR')", name="ck_supplier_rakuten_language"),
        sa.CheckConstraint("advertiser_mid > 0", name="ck_supplier_rakuten_advertiser_mid"),
        sa.CheckConstraint("max_results BETWEEN 1 AND 100", name="ck_supplier_rakuten_max_results"),
        sa.CheckConstraint("max_pages BETWEEN 1 AND 100", name="ck_supplier_rakuten_max_pages"),
        sa.CheckConstraint("sync_interval_minutes BETWEEN 15 AND 10080", name="ck_supplier_rakuten_sync_interval"),
        sa.CheckConstraint("sync_enabled = false OR approval_status = 'approved'", name="ck_supplier_rakuten_sync_requires_approval"),
    )
    op.create_index("ix_supplier_rakuten_configs_supplier_id", "supplier_rakuten_configs", ["supplier_id"])


def downgrade() -> None:
    op.drop_table("supplier_rakuten_configs")
