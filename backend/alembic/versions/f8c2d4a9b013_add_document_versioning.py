"""add document versioning

Revision ID: f8c2d4a9b013
Revises: e4b9c1a7d602
Create Date: 2026-08-12 13:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f8c2d4a9b013"
down_revision: Union[str, Sequence[str], None] = "e4b9c1a7d602"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("version", sa.Integer(), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "previous_document_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "version_group_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column("documents", sa.Column("is_latest", sa.Boolean(), nullable=True))

    op.execute(
        """
        UPDATE documents
        SET
            version = 1,
            version_group_id = id,
            is_latest = true
        WHERE version IS NULL
        """
    )

    op.alter_column("documents", "version", nullable=False)
    op.alter_column("documents", "version_group_id", nullable=False)
    op.alter_column("documents", "is_latest", nullable=False)

    op.create_index(
        op.f("ix_documents_previous_document_id"),
        "documents",
        ["previous_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_documents_version_group_id"),
        "documents",
        ["version_group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_documents_is_latest"),
        "documents",
        ["is_latest"],
        unique=False,
    )
    op.create_foreign_key(
        "documents_previous_document_id_fkey",
        "documents",
        "documents",
        ["previous_document_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "documents_previous_document_id_fkey",
        "documents",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_documents_is_latest"), table_name="documents")
    op.drop_index(op.f("ix_documents_version_group_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_previous_document_id"), table_name="documents")
    op.drop_column("documents", "is_latest")
    op.drop_column("documents", "version_group_id")
    op.drop_column("documents", "previous_document_id")
    op.drop_column("documents", "version")
