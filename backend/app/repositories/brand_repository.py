from uuid import UUID

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.models.product_research_candidate import ProductResearchCandidate
from app.repositories.base_repository import BaseRepository


class BrandRepository(BaseRepository[Brand]):
    SORT_COLUMNS = {
        "brand_name": Brand.brand_name, "luxury_tier": Brand.luxury_tier,
        "created_at": Brand.created_at, "updated_at": Brand.updated_at,
    }

    def __init__(self, db: AsyncSession):
        super().__init__(db, Brand)

    async def find_by_code(self, brand_code: str) -> Brand | None:
        return await self.db.scalar(select(Brand).where(Brand.brand_code == brand_code))

    async def find_many_by_ids(self, brand_ids: list[UUID]) -> list[Brand]:
        if not brand_ids:
            return []
        result = await self.db.execute(select(Brand).where(Brand.id.in_(set(brand_ids))))
        return list(result.scalars().all())

    async def list_paginated(self, *, q: str | None, luxury_tier: str | None,
        online_purchase_policy: str | None, is_research_enabled: bool | None,
        is_active: bool | None, page: int, page_size: int, sort_by: str, sort_order: str) -> dict:
        filters = []
        if q:
            filters.append(or_(Brand.brand_code.ilike(f"%{q}%"), Brand.brand_name.ilike(f"%{q}%")))
        if luxury_tier:
            filters.append(Brand.luxury_tier == luxury_tier)
        if online_purchase_policy:
            filters.append(Brand.online_purchase_policy == online_purchase_policy)
        if is_research_enabled is not None:
            filters.append(Brand.is_research_enabled == is_research_enabled)
        if is_active is not None:
            filters.append(Brand.is_active == is_active)
        total = int((await self.db.scalar(select(func.count(Brand.id)).where(*filters))) or 0)
        column = self.SORT_COLUMNS[sort_by]
        order = asc(column) if sort_order == "asc" else desc(column)
        result = await self.db.execute(select(Brand).where(*filters).order_by(order, Brand.id).offset((page - 1) * page_size).limit(page_size))
        return {"items": list(result.scalars().all()), "total": total}

    async def candidate_reference_count(self, brand_id: UUID) -> int:
        return int((await self.db.scalar(select(func.count()).select_from(ProductResearchCandidate).where(ProductResearchCandidate.brand_id == brand_id))) or 0)
