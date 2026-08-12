"""add document ingestion status

Revision ID: bfd4a41c0d3a
Revises: 166cad5ebad8
Create Date: 2026-08-12 11:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "bfd4a41c0d3a"
down_revision: Union[str, Sequence[str], None] = "166cad5ebad8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "ingestion_status",
            sa.String(length=50),
            nullable=True,
        ),
    )
    op.execute(
        """
        UPDATE documents
        SET ingestion_status = 'ready'
        WHERE ingestion_status IS NULL
        """
    )
    op.alter_column(
        "documents",
        "ingestion_status",
        nullable=False,
    )
    op.create_index(
        op.f("ix_documents_ingestion_status"),
        "documents",
        ["ingestion_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_ingestion_status"), table_name="documents")
    op.drop_column("documents", "ingestion_status")
