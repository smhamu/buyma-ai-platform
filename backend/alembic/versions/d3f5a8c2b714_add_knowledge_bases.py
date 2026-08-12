"""add knowledge bases

Revision ID: d3f5a8c2b714
Revises: c7a4d2e8f901
Create Date: 2026-08-12 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3f5a8c2b714"
down_revision: Union[str, Sequence[str], None] = "c7a4d2e8f901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_bases_name"),
        "knowledge_bases",
        ["name"],
        unique=False,
    )

    op.add_column(
        "documents",
        sa.Column("knowledge_base_id", sa.UUID(), nullable=True),
    )
    op.create_index(
        op.f("ix_documents_knowledge_base_id"),
        "documents",
        ["knowledge_base_id"],
        unique=False,
    )
    op.create_foreign_key(
        "documents_knowledge_base_id_fkey",
        "documents",
        "knowledge_bases",
        ["knowledge_base_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "documents_knowledge_base_id_fkey",
        "documents",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_documents_knowledge_base_id"),
        table_name="documents",
    )
    op.drop_column("documents", "knowledge_base_id")
    op.drop_index(op.f("ix_knowledge_bases_name"), table_name="knowledge_bases")
    op.drop_table("knowledge_bases")
