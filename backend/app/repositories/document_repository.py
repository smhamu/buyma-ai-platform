from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Document)

    async def find_by_knowledge_base_id(
        self,
        knowledge_base_id,
    ) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def find_by_checksum(
        self,
        checksum: str,
        knowledge_base_id: UUID | None = None,
    ) -> Document | None:
        query = select(Document).where(Document.checksum == checksum)

        if knowledge_base_id is None:
            query = query.where(Document.knowledge_base_id.is_(None))
        else:
            query = query.where(Document.knowledge_base_id == knowledge_base_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_latest_by_filename(
        self,
        *,
        knowledge_base_id: UUID | None,
        original_filename: str,
    ) -> Document | None:
        query = (
            select(Document)
            .where(
                Document.original_filename == original_filename,
                Document.is_latest.is_(True),
            )
            .order_by(Document.version.desc())
        )

        if knowledge_base_id is None:
            query = query.where(Document.knowledge_base_id.is_(None))
        else:
            query = query.where(Document.knowledge_base_id == knowledge_base_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_versions_by_group(
        self,
        version_group_id: UUID,
    ) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.version_group_id == version_group_id)
            .order_by(Document.version.asc())
        )
        return list(result.scalars().all())

    async def find_latest_by_version_group(
        self,
        version_group_id: UUID,
    ) -> Document | None:
        result = await self.db.execute(
            select(Document)
            .where(
                Document.version_group_id == version_group_id,
                Document.is_latest.is_(True),
            )
            .order_by(Document.version.desc())
        )
        return result.scalar_one_or_none()
