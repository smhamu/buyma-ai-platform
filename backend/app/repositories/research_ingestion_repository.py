from uuid import UUID

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_source_product import ResearchSourceProduct
from app.repositories.base_repository import BaseRepository


class ResearchIngestionRepository(BaseRepository[ResearchSourceProduct]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ResearchSourceProduct)

    async def find_accessible(self, source_id: UUID, owner_id: UUID, is_admin: bool):
        filters = [ResearchSourceProduct.id == source_id]
        if not is_admin:
            filters.append(ResearchSourceProduct.owner_user_id == owner_id)
        return await self.db.scalar(select(ResearchSourceProduct).where(*filters))

    async def find_duplicate(self, supplier_id: UUID, normalized_url: str, external_id: str | None = None):
        clauses = [ResearchSourceProduct.normalized_source_url == normalized_url]
        if external_id:
            clauses.append(ResearchSourceProduct.external_product_id == external_id)
        return await self.db.scalar(select(ResearchSourceProduct).where(ResearchSourceProduct.supplier_id == supplier_id, or_(*clauses)))

    async def find_filtered(self, *, owner_id: UUID | None, supplier_id: UUID | None, brand_id: UUID | None, source_type: str | None, status: str | None, q: str | None, page: int, page_size: int):
        filters = []
        if owner_id: filters.append(ResearchSourceProduct.owner_user_id == owner_id)
        if supplier_id: filters.append(ResearchSourceProduct.supplier_id == supplier_id)
        if brand_id: filters.append(ResearchSourceProduct.brand_id == brand_id)
        if source_type: filters.append(ResearchSourceProduct.source_type == source_type)
        if status: filters.append(ResearchSourceProduct.processing_status == status)
        if q:
            term = f"%{q}%"
            filters.append(or_(ResearchSourceProduct.normalized_title.ilike(term), ResearchSourceProduct.source_url.ilike(term), ResearchSourceProduct.external_product_id.ilike(term)))
        total = int(await self.db.scalar(select(func.count()).select_from(ResearchSourceProduct).where(*filters)) or 0)
        rows = await self.db.scalars(select(ResearchSourceProduct).where(*filters).order_by(desc(ResearchSourceProduct.created_at), asc(ResearchSourceProduct.id)).offset((page - 1) * page_size).limit(page_size))
        return {"items": list(rows), "total": total}
