"""add brand master and candidate brand relation

Revision ID: c4f82a1d6e93
Revises: b7e31c9a2d40
Create Date: 2026-08-15 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c4f82a1d6e93"
down_revision: Union[str, Sequence[str], None] = "b7e31c9a2d40"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("suppliers", sa.Column("supplier_type", sa.String(32), server_default="unknown", nullable=False))
    op.create_check_constraint("ck_suppliers_type", "suppliers", "supplier_type IN ('authorized_retailer','department_store','boutique','marketplace','other','unknown')")
    op.create_index("ix_suppliers_supplier_type", "suppliers", ["supplier_type"])
    op.alter_column("suppliers", "supplier_type", server_default=None)

    op.create_table(
        "brands",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("brand_code", sa.String(100), nullable=False),
        sa.Column("brand_name", sa.String(255), nullable=False),
        sa.Column("luxury_tier", sa.String(32), nullable=False),
        sa.Column("official_site_url", sa.String(2048), nullable=True),
        sa.Column("online_purchase_policy", sa.String(32), nullable=False),
        sa.Column("purchase_restriction_notes", sa.Text(), nullable=True),
        sa.Column("is_research_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brand_code"),
        sa.CheckConstraint("luxury_tier IN ('ultra_luxury','luxury','premium')", name="ck_brands_luxury_tier"),
        sa.CheckConstraint("online_purchase_policy IN ('normal','limited','category_limited','boutique_only','research_only','unknown')", name="ck_brands_purchase_policy"),
    )
    op.create_index("ix_brands_brand_code", "brands", ["brand_code"], unique=True)
    op.create_index("ix_brands_brand_name", "brands", ["brand_name"])
    op.create_index("ix_brands_luxury_tier", "brands", ["luxury_tier"])
    op.create_index("ix_brands_online_purchase_policy", "brands", ["online_purchase_policy"])

    op.create_table(
        "supplier_brands",
        sa.Column("supplier_id", sa.UUID(), nullable=False),
        sa.Column("brand_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("supplier_id", "brand_id"),
    )
    op.create_index("ix_supplier_brands_brand_id", "supplier_brands", ["brand_id"])

    op.add_column("product_research_candidates", sa.Column("brand_id", sa.UUID(), nullable=True))
    op.add_column("product_research_candidates", sa.Column("online_purchase_available", sa.Boolean(), server_default=sa.true(), nullable=False))

    # Preserve every existing textual brand as a master record. Known luxury
    # brands receive canonical codes; unknown legacy names receive stable hashes.
    op.execute("""
        WITH source AS (
            SELECT lower(trim(coalesce(nullif(brand_name, ''), 'Unknown Legacy Brand'))) AS normalized_name,
                   min(trim(coalesce(nullif(brand_name, ''), 'Unknown Legacy Brand'))) AS display_name
            FROM product_research_candidates
            GROUP BY lower(trim(coalesce(nullif(brand_name, ''), 'Unknown Legacy Brand')))
        )
        INSERT INTO brands (id, brand_code, brand_name, luxury_tier, online_purchase_policy, is_research_enabled, is_active)
        SELECT gen_random_uuid(),
               CASE normalized_name
                   WHEN 'hermès' THEN 'hermes' WHEN 'hermes' THEN 'hermes'
                   WHEN 'chanel' THEN 'chanel' WHEN 'gucci' THEN 'gucci'
                   WHEN 'prada' THEN 'prada' WHEN 'saint laurent' THEN 'saint_laurent'
                   WHEN 'bottega veneta' THEN 'bottega_veneta' WHEN 'loewe' THEN 'loewe'
                   WHEN 'dior' THEN 'dior' WHEN 'celine' THEN 'celine'
                   ELSE 'legacy_' || substr(md5(normalized_name), 1, 24)
               END,
               display_name,
               CASE WHEN normalized_name IN ('hermès','hermes','chanel') THEN 'ultra_luxury' ELSE 'luxury' END,
               CASE WHEN normalized_name IN ('hermès','hermes','chanel') THEN 'research_only' ELSE 'unknown' END,
               true, true
        FROM source
        ON CONFLICT (brand_code) DO NOTHING
    """)
    op.execute("""
        UPDATE product_research_candidates candidate
        SET brand_id = brand.id
        FROM brands brand
        WHERE brand.brand_code = CASE lower(trim(coalesce(nullif(candidate.brand_name, ''), 'Unknown Legacy Brand')))
            WHEN 'hermès' THEN 'hermes' WHEN 'hermes' THEN 'hermes'
            WHEN 'chanel' THEN 'chanel' WHEN 'gucci' THEN 'gucci'
            WHEN 'prada' THEN 'prada' WHEN 'saint laurent' THEN 'saint_laurent'
            WHEN 'bottega veneta' THEN 'bottega_veneta' WHEN 'loewe' THEN 'loewe'
            WHEN 'dior' THEN 'dior' WHEN 'celine' THEN 'celine'
            ELSE 'legacy_' || substr(md5(lower(trim(coalesce(nullif(candidate.brand_name, ''), 'Unknown Legacy Brand')))), 1, 24)
        END
    """)
    op.alter_column("product_research_candidates", "brand_id", nullable=False)
    op.create_foreign_key("product_research_candidates_brand_id_fkey", "product_research_candidates", "brands", ["brand_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_product_research_candidates_brand_id", "product_research_candidates", ["brand_id"])
    op.drop_index("ix_product_research_candidates_brand_name", table_name="product_research_candidates")
    op.drop_column("product_research_candidates", "brand_name")


def downgrade() -> None:
    op.add_column("product_research_candidates", sa.Column("brand_name", sa.String(255), nullable=True))
    op.execute("UPDATE product_research_candidates c SET brand_name = b.brand_name FROM brands b WHERE c.brand_id = b.id")
    op.create_index("ix_product_research_candidates_brand_name", "product_research_candidates", ["brand_name"])
    op.drop_index("ix_product_research_candidates_brand_id", table_name="product_research_candidates")
    op.drop_constraint("product_research_candidates_brand_id_fkey", "product_research_candidates", type_="foreignkey")
    op.drop_column("product_research_candidates", "online_purchase_available")
    op.drop_column("product_research_candidates", "brand_id")
    op.drop_table("supplier_brands")
    op.drop_table("brands")
    op.drop_index("ix_suppliers_supplier_type", table_name="suppliers")
    op.drop_constraint("ck_suppliers_type", "suppliers", type_="check")
    op.drop_column("suppliers", "supplier_type")
