"""add document cascade delete

Revision ID: c7a4d2e8f901
Revises: bfd4a41c0d3a
Create Date: 2026-08-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c7a4d2e8f901"
down_revision: Union[str, Sequence[str], None] = "bfd4a41c0d3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "document_chunks_document_id_fkey",
        "document_chunks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "document_chunks_document_id_fkey",
        "document_chunks",
        "documents",
        ["document_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "embedding_jobs_document_id_fkey",
        "embedding_jobs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embedding_jobs_document_id_fkey",
        "embedding_jobs",
        "documents",
        ["document_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "embedding_jobs_chunk_id_fkey",
        "embedding_jobs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embedding_jobs_chunk_id_fkey",
        "embedding_jobs",
        "document_chunks",
        ["chunk_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "embeddings_document_id_fkey",
        "embeddings",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embeddings_document_id_fkey",
        "embeddings",
        "documents",
        ["document_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "embeddings_chunk_id_fkey",
        "embeddings",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embeddings_chunk_id_fkey",
        "embeddings",
        "document_chunks",
        ["chunk_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "embeddings_embedding_job_id_fkey",
        "embeddings",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embeddings_embedding_job_id_fkey",
        "embeddings",
        "embedding_jobs",
        ["embedding_job_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "embeddings_embedding_job_id_fkey",
        "embeddings",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embeddings_embedding_job_id_fkey",
        "embeddings",
        "embedding_jobs",
        ["embedding_job_id"],
        ["id"],
    )

    op.drop_constraint(
        "embeddings_chunk_id_fkey",
        "embeddings",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embeddings_chunk_id_fkey",
        "embeddings",
        "document_chunks",
        ["chunk_id"],
        ["id"],
    )

    op.drop_constraint(
        "embeddings_document_id_fkey",
        "embeddings",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embeddings_document_id_fkey",
        "embeddings",
        "documents",
        ["document_id"],
        ["id"],
    )

    op.drop_constraint(
        "embedding_jobs_chunk_id_fkey",
        "embedding_jobs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embedding_jobs_chunk_id_fkey",
        "embedding_jobs",
        "document_chunks",
        ["chunk_id"],
        ["id"],
    )

    op.drop_constraint(
        "embedding_jobs_document_id_fkey",
        "embedding_jobs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "embedding_jobs_document_id_fkey",
        "embedding_jobs",
        "documents",
        ["document_id"],
        ["id"],
    )

    op.drop_constraint(
        "document_chunks_document_id_fkey",
        "document_chunks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "document_chunks_document_id_fkey",
        "document_chunks",
        "documents",
        ["document_id"],
        ["id"],
    )
