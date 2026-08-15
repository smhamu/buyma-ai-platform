"""add research ingestion

Revision ID: d9a41f6c8b20
Revises: c4f82a1d6e93
"""
from alembic import op
import sqlalchemy as sa

revision = "d9a41f6c8b20"
down_revision = "c4f82a1d6e93"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name, column in (
        ("ingestion_source_type", sa.Column("ingestion_source_type", sa.String(32), nullable=False, server_default="manual")),
        ("automated_fetch_enabled", sa.Column("automated_fetch_enabled", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("terms_status", sa.Column("terms_status", sa.String(32), nullable=False, server_default="unchecked")),
        ("robots_status", sa.Column("robots_status", sa.String(32), nullable=False, server_default="unchecked")),
        ("terms_checked_at", sa.Column("terms_checked_at", sa.DateTime(timezone=True))),
        ("robots_checked_at", sa.Column("robots_checked_at", sa.DateTime(timezone=True))),
        ("official_api_available", sa.Column("official_api_available", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("research_policy_notes", sa.Column("research_policy_notes", sa.Text())),
        ("parser_key", sa.Column("parser_key", sa.String(100))),
        ("request_interval_seconds", sa.Column("request_interval_seconds", sa.Integer())),
        ("last_fetch_at", sa.Column("last_fetch_at", sa.DateTime(timezone=True))),
    ): op.add_column("suppliers", column)
    op.create_check_constraint("ck_suppliers_ingestion_source", "suppliers", "ingestion_source_type IN ('manual','url_manual','csv','official_api','structured_data','html_parser','disabled')")
    op.create_check_constraint("ck_suppliers_terms_status", "suppliers", "terms_status IN ('unchecked','allowed','restricted','prohibited','unknown')")
    op.create_check_constraint("ck_suppliers_robots_status", "suppliers", "robots_status IN ('unchecked','allowed','restricted','disallowed','unknown')")

    op.create_table(
        "research_source_products",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("owner_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", sa.UUID(), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand_id", sa.UUID(), sa.ForeignKey("brands.id", ondelete="SET NULL")),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("normalized_source_url", sa.String(2048), nullable=False),
        sa.Column("external_product_id", sa.String(255)),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
        sa.Column("raw_title", sa.String(500)), sa.Column("raw_brand", sa.String(255)),
        sa.Column("raw_price", sa.Numeric(18, 2)), sa.Column("raw_currency", sa.String(3)),
        sa.Column("raw_availability", sa.String(32)), sa.Column("raw_payload", sa.JSON()),
        sa.Column("normalized_title", sa.String(500)), sa.Column("normalized_price", sa.Numeric(18, 2)),
        sa.Column("normalized_currency", sa.String(3)), sa.Column("normalized_availability", sa.String(32)),
        sa.Column("processing_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("error_code", sa.String(100)), sa.Column("error_message", sa.Text()),
        sa.Column("candidate_id", sa.UUID()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("supplier_id", "external_product_id", name="uq_source_supplier_external"),
        sa.UniqueConstraint("supplier_id", "normalized_source_url", name="uq_source_supplier_url"),
        sa.CheckConstraint("source_type IN ('manual','url_manual','csv','official_api','structured_data','html_parser','disabled')", name="ck_source_type"),
        sa.CheckConstraint("processing_status IN ('pending','fetched','normalized','matched','candidate_created','rejected','failed')", name="ck_source_processing_status"),
    )
    for column in ("owner_user_id", "supplier_id", "brand_id", "source_type", "processing_status"):
        op.create_index(f"ix_research_source_products_{column}", "research_source_products", [column])
    op.add_column("product_research_candidates", sa.Column("source_product_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_candidate_source_product", "product_research_candidates", "research_source_products", ["source_product_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_product_research_candidates_source_product_id", "product_research_candidates", ["source_product_id"], unique=True)
    op.create_foreign_key("fk_source_candidate", "research_source_products", "product_research_candidates", ["candidate_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_source_candidate", "research_source_products", type_="foreignkey")
    op.drop_index("ix_product_research_candidates_source_product_id", table_name="product_research_candidates")
    op.drop_constraint("fk_candidate_source_product", "product_research_candidates", type_="foreignkey")
    op.drop_column("product_research_candidates", "source_product_id")
    op.drop_table("research_source_products")
    op.drop_constraint("ck_suppliers_robots_status", "suppliers", type_="check")
    op.drop_constraint("ck_suppliers_terms_status", "suppliers", type_="check")
    op.drop_constraint("ck_suppliers_ingestion_source", "suppliers", type_="check")
    for column in ("last_fetch_at", "request_interval_seconds", "parser_key", "research_policy_notes", "official_api_available", "robots_checked_at", "terms_checked_at", "robots_status", "terms_status", "automated_fetch_enabled", "ingestion_source_type"):
        op.drop_column("suppliers", column)
