from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier
from app.repositories.base_repository import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    SORT_COLUMNS = {"name": Supplier.name, "country_code": Supplier.country_code, "created_at": Supplier.created_at, "updated_at": Supplier.updated_at}
    def __init__(self, db: AsyncSession):
        super().__init__(db, Supplier)

    async def find_by_id_and_owner(self, supplier_id: UUID, owner_user_id: UUID) -> Supplier | None:
        result = await self.db.execute(
            select(Supplier).where(Supplier.id == supplier_id, Supplier.owner_user_id == owner_user_id)
        )
        return result.scalar_one_or_none()

    async def find_by_name(self, name: str, owner_user_id: UUID | None = None) -> Supplier | None:
        filters = [func.lower(Supplier.name) == name.strip().lower()]
        if owner_user_id is not None:
            filters.append(Supplier.owner_user_id == owner_user_id)
        return await self.db.scalar(select(Supplier).where(*filters))

    async def find_all_filtered(
        self, *, owner_user_id: UUID | None, country: str | None, supplier_type: str | None, ships_to_japan: bool | None,
        buyma_allowed_status: str | None, research_status: str | None, is_active: bool | None,
        page: int, page_size: int, sort_by: str, sort_order: str
    ) -> dict:
        filters = []
        if owner_user_id is not None:
            filters.append(Supplier.owner_user_id == owner_user_id)
        if country:
            filters.append(Supplier.country_code == country)
        if supplier_type:
            filters.append(Supplier.supplier_type == supplier_type)
        if ships_to_japan is not None:
            filters.append(Supplier.ships_to_japan == ships_to_japan)
        if buyma_allowed_status:
            filters.append(Supplier.buyma_allowed_status == buyma_allowed_status)
        if research_status:
            filters.append(Supplier.research_status == research_status)
        if is_active is not None:
            filters.append(Supplier.is_active == is_active)
        total = int((await self.db.scalar(select(func.count(Supplier.id)).where(*filters))) or 0)
        column = self.SORT_COLUMNS[sort_by]
        order = asc(column) if sort_order == "asc" else desc(column)
        result = await self.db.execute(select(Supplier).where(*filters).order_by(order, Supplier.id).offset((page - 1) * page_size).limit(page_size))
        return {"items": list(result.scalars().unique().all()), "total": total}
