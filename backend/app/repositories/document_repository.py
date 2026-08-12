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
