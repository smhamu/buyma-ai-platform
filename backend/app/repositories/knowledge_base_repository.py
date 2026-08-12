from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase
from app.repositories.base_repository import BaseRepository


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, KnowledgeBase)

    async def find_by_id_and_owner(
        self,
        knowledge_base_id: UUID,
        owner_user_id: UUID,
    ) -> KnowledgeBase | None:
        result = await self.db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBase.owner_user_id == owner_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_all_by_owner(
        self,
        owner_user_id: UUID,
    ) -> list[KnowledgeBase]:
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.owner_user_id == owner_user_id)
            .order_by(KnowledgeBase.created_at.desc())
        )
        return list(result.scalars().all())
