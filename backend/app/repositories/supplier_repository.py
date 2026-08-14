from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier
from app.repositories.base_repository import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Supplier)

    async def find_by_id_and_owner(self, supplier_id: UUID, owner_user_id: UUID) -> Supplier | None:
        result = await self.db.execute(
            select(Supplier).where(Supplier.id == supplier_id, Supplier.owner_user_id == owner_user_id)
        )
        return result.scalar_one_or_none()

    async def find_all_filtered(
        self, *, owner_user_id: UUID | None, country: str | None, ships_to_japan: bool | None,
        buyma_allowed_status: str | None, research_status: str | None, is_active: bool | None
    ) -> list[Supplier]:
        query = select(Supplier)
        if owner_user_id is not None:
            query = query.where(Supplier.owner_user_id == owner_user_id)
        if country:
            query = query.where(Supplier.country_code == country)
        if ships_to_japan is not None:
            query = query.where(Supplier.ships_to_japan == ships_to_japan)
        if buyma_allowed_status:
            query = query.where(Supplier.buyma_allowed_status == buyma_allowed_status)
        if research_status:
            query = query.where(Supplier.research_status == research_status)
        if is_active is not None:
            query = query.where(Supplier.is_active == is_active)
        result = await self.db.execute(query.order_by(Supplier.created_at.desc()))
        return list(result.scalars().all())
