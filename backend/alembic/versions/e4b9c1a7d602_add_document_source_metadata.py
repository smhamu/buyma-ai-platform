"""add document source metadata

Revision ID: e4b9c1a7d602
Revises: d3f5a8c2b714
Create Date: 2026-08-12 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4b9c1a7d602"
down_revision: Union[str, Sequence[str], None] = "d3f5a8c2b714"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("original_filename", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("mime_type", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("file_size", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("checksum", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_documents_checksum"),
        "documents",
        ["checksum"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_checksum"), table_name="documents")
    op.drop_column("documents", "checksum")
    op.drop_column("documents", "file_size")
    op.drop_column("documents", "mime_type")
    op.drop_column("documents", "original_filename")
