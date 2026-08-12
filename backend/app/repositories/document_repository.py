from uuid import UUID

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def search_by_knowledge_base(
        self,
        *,
        knowledge_base_id: UUID,
        page: int = 1,
        page_size: int = 20,
        q: str | None = None,
        status: str | None = None,
        ingestion_status: str | None = None,
        is_latest: bool | None = True,
        source_type: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        filters = [Document.knowledge_base_id == knowledge_base_id]

        if q:
            keyword = f"%{q}%"
            filters.append(
                or_(
                    Document.title.ilike(keyword),
                    Document.original_filename.ilike(keyword),
                )
            )

        if status:
            filters.append(Document.status == status)

        if ingestion_status:
            filters.append(Document.ingestion_status == ingestion_status)

        if is_latest is not None:
            filters.append(Document.is_latest == is_latest)

        if source_type:
            filters.append(Document.source_type == source_type)

        total_result = await self.db.execute(
            select(func.count(Document.id)).where(*filters)
        )
        total = int(total_result.scalar_one())

        sort_columns = {
            "created_at": Document.created_at,
            "updated_at": Document.updated_at,
            "title": Document.title,
            "version": Document.version,
            "ingestion_status": Document.ingestion_status,
        }
        sort_column = sort_columns.get(sort_by, Document.created_at)
        order_expression = (
            asc(sort_column) if sort_order == "asc" else desc(sort_column)
        )
        offset = (page - 1) * page_size

        result = await self.db.execute(
            select(Document)
            .where(*filters)
            .order_by(order_expression)
            .offset(offset)
            .limit(page_size)
        )

        return {
            "items": list(result.scalars().all()),
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
        }

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
