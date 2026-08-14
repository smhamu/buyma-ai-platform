"""add EU supplier and product research candidate tables

Revision ID: b7e31c9a2d40
Revises: aa12f3d4b567
Create Date: 2026-08-15 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7e31c9a2d40"
down_revision: Union[str, Sequence[str], None] = "aa12f3d4b567"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "suppliers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("website_url", sa.String(2048), nullable=False),
        sa.Column("default_currency", sa.String(3), nullable=False),
        sa.Column("ships_to_japan", sa.Boolean(), nullable=False),
        sa.Column("vat_policy", sa.String(32), nullable=False),
        sa.Column("vat_rate", sa.Numeric(7, 6), nullable=True),
        sa.Column("japan_shipping_cost", sa.Numeric(18, 2), nullable=True),
        sa.Column("buyma_allowed_status", sa.String(32), nullable=False),
        sa.Column("buyma_status_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("research_status", sa.String(32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("country_code IN ('FR','IT','DE','ES','NL','BE','AT','IE','PT')", name="ck_suppliers_eu_country"),
        sa.CheckConstraint("default_currency IN ('EUR','JPY','GBP','CHF','USD')", name="ck_suppliers_currency"),
        sa.CheckConstraint("vat_policy IN ('included','excluded_for_export','not_refunded','unknown')", name="ck_suppliers_vat_policy"),
        sa.CheckConstraint("vat_rate IS NULL OR (vat_rate >= 0 AND vat_rate <= 1)", name="ck_suppliers_vat_rate"),
        sa.CheckConstraint("buyma_allowed_status IN ('unchecked','allowed','caution','prohibited')", name="ck_suppliers_buyma_status"),
    )
    op.create_index("ix_suppliers_owner_user_id", "suppliers", ["owner_user_id"])
    op.create_index("ix_suppliers_name", "suppliers", ["name"])
    op.create_index("ix_suppliers_country_code", "suppliers", ["country_code"])
    op.create_index("ix_suppliers_buyma_allowed_status", "suppliers", ["buyma_allowed_status"])
    op.create_index("ix_suppliers_research_status", "suppliers", ["research_status"])

    op.create_table(
        "product_research_candidates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("supplier_id", sa.UUID(), nullable=False),
        sa.Column("supplier_product_url", sa.String(2048), nullable=False),
        sa.Column("supplier_product_code", sa.String(255), nullable=True),
        sa.Column("product_name", sa.String(500), nullable=False),
        sa.Column("brand_name", sa.String(255), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("supplier_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("supplier_currency", sa.String(3), nullable=False),
        sa.Column("vat_policy", sa.String(32), nullable=False),
        sa.Column("vat_rate", sa.Numeric(7, 6), nullable=True),
        sa.Column("export_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("japan_shipping_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(18, 6), nullable=False),
        sa.Column("supplier_cost_jpy", sa.Numeric(18, 0), nullable=False),
        sa.Column("estimated_import_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("estimated_other_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(18, 0), nullable=False),
        sa.Column("buyma_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("buyma_fee_rate", sa.Numeric(7, 6), nullable=False),
        sa.Column("buyma_fee", sa.Numeric(18, 0), nullable=False),
        sa.Column("profit_amount", sa.Numeric(18, 0), nullable=False),
        sa.Column("profit_rate", sa.Numeric(9, 6), nullable=False),
        sa.Column("availability_status", sa.String(32), nullable=False),
        sa.Column("research_status", sa.String(32), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("supplier_price > 0 AND exchange_rate > 0 AND buyma_price > 0", name="ck_research_positive_prices"),
        sa.CheckConstraint("buyma_fee_rate >= 0 AND buyma_fee_rate <= 1", name="ck_research_fee_rate"),
        sa.CheckConstraint("vat_rate IS NULL OR (vat_rate >= 0 AND vat_rate <= 1)", name="ck_research_vat_rate"),
    )
    for column in ("owner_user_id", "supplier_id", "brand_name", "supplier_currency", "profit_amount", "profit_rate", "availability_status", "research_status"):
        op.create_index(f"ix_product_research_candidates_{column}", "product_research_candidates", [column])


def downgrade() -> None:
    op.drop_table("product_research_candidates")
    op.drop_table("suppliers")
