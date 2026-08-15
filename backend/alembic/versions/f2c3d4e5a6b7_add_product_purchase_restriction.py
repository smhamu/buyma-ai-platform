"""add product purchase restriction

Revision ID: f2c3d4e5a6b7
Revises: e1b2c3d4e5f6
"""

from alembic import op
import sqlalchemy as sa


revision = "f2c3d4e5a6b7"
down_revision = "e1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable is deliberate: existing records retain an unknown/unreviewed state
    # without inventing a normal purchase policy during migration.
    op.add_column(
        "product_research_candidates",
        sa.Column("purchase_restriction", sa.String(length=32), nullable=True),
    )
    op.create_index(
        op.f("ix_product_research_candidates_purchase_restriction"),
        "product_research_candidates",
        ["purchase_restriction"],
        unique=False,
    )
    op.add_column(
        "research_source_products",
        sa.Column("purchase_restriction", sa.String(length=32), nullable=True),
    )
    op.create_index(
        op.f("ix_research_source_products_purchase_restriction"),
        "research_source_products",
        ["purchase_restriction"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_research_source_products_purchase_restriction"),
        table_name="research_source_products",
    )
    op.drop_column("research_source_products", "purchase_restriction")
    op.drop_index(
        op.f("ix_product_research_candidates_purchase_restriction"),
        table_name="product_research_candidates",
    )
    op.drop_column("product_research_candidates", "purchase_restriction")
