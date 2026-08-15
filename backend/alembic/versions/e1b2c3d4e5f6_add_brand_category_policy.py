"""add brand category purchase policy

Revision ID: e1b2c3d4e5f6
Revises: d9a41f6c8b20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e1b2c3d4e5f6"
down_revision = "d9a41f6c8b20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category_code", sa.String(100), nullable=False, unique=True),
        sa.Column("category_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("category_code ~ '^[a-z][a-z0-9_]*$'", name="ck_product_categories_code"),
    )
    op.create_index("ix_product_categories_category_code", "product_categories", ["category_code"], unique=True)
    op.create_table(
        "brand_category_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("online_purchase_policy", sa.String(32), nullable=False),
        sa.Column("research_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("policy_notes", sa.Text()),
        sa.Column("checked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("brand_id", "category_id", name="uq_brand_category_policy"),
        sa.CheckConstraint("online_purchase_policy IN ('normal','limited','category_limited','boutique_only','research_only','unknown')", name="ck_brand_category_policy_value"),
    )
    op.create_index("ix_brand_category_policies_brand_id", "brand_category_policies", ["brand_id"])
    op.create_index("ix_brand_category_policies_category_id", "brand_category_policies", ["category_id"])
    for table in ("product_research_candidates", "research_source_products"):
        op.add_column(table, sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(f"fk_{table}_category", table, "product_categories", ["category_id"], ["id"], ondelete="SET NULL")
        op.create_index(f"ix_{table}_category_id", table, ["category_id"])


def downgrade() -> None:
    for table in ("research_source_products", "product_research_candidates"):
        op.drop_index(f"ix_{table}_category_id", table_name=table)
        op.drop_constraint(f"fk_{table}_category", table, type_="foreignkey")
        op.drop_column(table, "category_id")
    op.drop_table("brand_category_policies")
    op.drop_table("product_categories")
