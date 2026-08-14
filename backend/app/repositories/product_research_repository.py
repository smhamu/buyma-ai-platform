from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_research_candidate import ProductResearchCandidate
from app.models.supplier import Supplier
from app.repositories.base_repository import BaseRepository


class ProductResearchRepository(BaseRepository[ProductResearchCandidate]):
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
        self, *, owner_user_id: UUID | None, brand: str | None, supplier_id: UUID | None,
        country: str | None, currency: str | None, research_status: str | None,
        availability_status: str | None, buyma_allowed_status: str | None,
        min_profit_amount: Decimal | None, min_profit_rate: Decimal | None,
        ships_to_japan: bool | None
    ) -> list[ProductResearchCandidate]:
        query = select(ProductResearchCandidate).join(
            Supplier, Supplier.id == ProductResearchCandidate.supplier_id
        )
        if owner_user_id is not None:
            query = query.where(ProductResearchCandidate.owner_user_id == owner_user_id)
        if brand:
            query = query.where(ProductResearchCandidate.brand_name.ilike(f"%{brand}%"))
        if supplier_id:
            query = query.where(ProductResearchCandidate.supplier_id == supplier_id)
        if country:
            query = query.where(Supplier.country_code == country)
        if currency:
            query = query.where(ProductResearchCandidate.supplier_currency == currency)
        if research_status:
            query = query.where(ProductResearchCandidate.research_status == research_status)
        if availability_status:
            query = query.where(ProductResearchCandidate.availability_status == availability_status)
        if buyma_allowed_status:
            query = query.where(Supplier.buyma_allowed_status == buyma_allowed_status)
        if min_profit_amount is not None:
            query = query.where(ProductResearchCandidate.profit_amount >= min_profit_amount)
        if min_profit_rate is not None:
            query = query.where(ProductResearchCandidate.profit_rate >= min_profit_rate)
        if ships_to_japan is not None:
            query = query.where(Supplier.ships_to_japan == ships_to_japan)
        result = await self.db.execute(query.order_by(ProductResearchCandidate.created_at.desc()))
        return list(result.scalars().all())
