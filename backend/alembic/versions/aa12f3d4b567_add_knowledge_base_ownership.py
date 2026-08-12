"""add knowledge base ownership

Revision ID: aa12f3d4b567
Revises: f8c2d4a9b013
Create Date: 2026-08-12 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "aa12f3d4b567"
down_revision: Union[str, Sequence[str], None] = "f8c2d4a9b013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "knowledge_bases",
        sa.Column("owner_user_id", sa.UUID(), nullable=True),
    )
    op.create_index(
        op.f("ix_knowledge_bases_owner_user_id"),
        "knowledge_bases",
        ["owner_user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "knowledge_bases_owner_user_id_fkey",
        "knowledge_bases",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute(
        """
        UPDATE knowledge_bases kb
        SET owner_user_id = (
            SELECT id
            FROM users
            WHERE role = 'admin'
            ORDER BY created_at ASC
            LIMIT 1
        )
        WHERE kb.owner_user_id IS NULL
        """
    )
    op.alter_column(
        "knowledge_bases",
        "owner_user_id",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_constraint(
        "knowledge_bases_owner_user_id_fkey",
        "knowledge_bases",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_knowledge_bases_owner_user_id"),
        table_name="knowledge_bases",
    )
    op.drop_column("knowledge_bases", "owner_user_id")
