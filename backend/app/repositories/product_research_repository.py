from decimal import Decimal
from uuid import UUID

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_research_candidate import ProductResearchCandidate
from app.models.supplier import Supplier
from app.models.brand import Brand
from app.repositories.base_repository import BaseRepository


class ProductResearchRepository(BaseRepository[ProductResearchCandidate]):
    SORT_COLUMNS = {
        "product_name": ProductResearchCandidate.product_name, "supplier_price": ProductResearchCandidate.supplier_price,
        "buyma_price": ProductResearchCandidate.buyma_price, "profit_amount": ProductResearchCandidate.profit_amount,
        "profit_rate": ProductResearchCandidate.profit_rate, "checked_at": ProductResearchCandidate.checked_at,
        "created_at": ProductResearchCandidate.created_at,
    }
    def __init__(self, db: AsyncSession):
        super().__init__(db, ProductResearchCandidate)

    async def find_by_id_and_owner(self, candidate_id: UUID, owner_user_id: UUID):
        result = await self.db.execute(
            select(ProductResearchCandidate).where(
                ProductResearchCandidate.id == candidate_id,
                ProductResearchCandidate.owner_user_id == owner_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_all_filtered(
        self, *, owner_user_id: UUID | None, q: str | None, brand: str | None,
        brand_id: UUID | None, brand_code: str | None, supplier_id: UUID | None,
        country: str | None, currency: str | None, research_status: str | None,
        availability_status: str | None, buyma_allowed_status: str | None,
        min_profit_amount: Decimal | None, min_profit_rate: Decimal | None,
        ships_to_japan: bool | None, page: int, page_size: int, sort_by: str, sort_order: str
    ) -> dict:
        query = select(ProductResearchCandidate).join(
            Supplier, Supplier.id == ProductResearchCandidate.supplier_id
        ).join(Brand, Brand.id == ProductResearchCandidate.brand_id)
        filters = []
        if owner_user_id is not None:
            filters.append(ProductResearchCandidate.owner_user_id == owner_user_id)
        if q:
            filters.append(or_(ProductResearchCandidate.product_name.ilike(f"%{q}%"), ProductResearchCandidate.supplier_product_code.ilike(f"%{q}%")))
        if brand:
            filters.append(Brand.brand_name.ilike(f"%{brand}%"))
        if brand_id:
            filters.append(ProductResearchCandidate.brand_id == brand_id)
        if brand_code:
            filters.append(Brand.brand_code == brand_code)
        if supplier_id:
            filters.append(ProductResearchCandidate.supplier_id == supplier_id)
        if country:
            filters.append(Supplier.country_code == country)
        if currency:
            filters.append(ProductResearchCandidate.supplier_currency == currency)
        if research_status:
            filters.append(ProductResearchCandidate.research_status == research_status)
        if availability_status:
            filters.append(ProductResearchCandidate.availability_status == availability_status)
        if buyma_allowed_status:
            filters.append(Supplier.buyma_allowed_status == buyma_allowed_status)
        if min_profit_amount is not None:
            filters.append(ProductResearchCandidate.profit_amount >= min_profit_amount)
        if min_profit_rate is not None:
            filters.append(ProductResearchCandidate.profit_rate >= min_profit_rate)
        if ships_to_japan is not None:
            filters.append(Supplier.ships_to_japan == ships_to_japan)
        total = int((await self.db.scalar(select(func.count(ProductResearchCandidate.id)).join(Supplier).join(Brand).where(*filters))) or 0)
        column = self.SORT_COLUMNS[sort_by]
        order = asc(column) if sort_order == "asc" else desc(column)
        result = await self.db.execute(query.where(*filters).order_by(order, ProductResearchCandidate.id).offset((page - 1) * page_size).limit(page_size))
        return {"items": list(result.scalars().all()), "total": total}
