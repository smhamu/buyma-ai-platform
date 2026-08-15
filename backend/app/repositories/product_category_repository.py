from uuid import UUID

from sqlalchemy import select

from app.models.product_category import BrandCategoryPolicy, ProductCategory
from app.repositories.base_repository import BaseRepository


class ProductCategoryRepository(BaseRepository[ProductCategory]):
    def __init__(self, db):
        super().__init__(db, ProductCategory)

    async def find_active(self):
        result = await self.db.scalars(select(ProductCategory).where(ProductCategory.is_active.is_(True)).order_by(ProductCategory.category_name))
        return list(result.all())

    async def find_by_code(self, code: str):
        return await self.db.scalar(select(ProductCategory).where(ProductCategory.category_code == code))


class BrandCategoryPolicyRepository(BaseRepository[BrandCategoryPolicy]):
    def __init__(self, db):
        super().__init__(db, BrandCategoryPolicy)

    async def list_for_brand(self, brand_id: UUID):
        result = await self.db.scalars(select(BrandCategoryPolicy).where(BrandCategoryPolicy.brand_id == brand_id).order_by(BrandCategoryPolicy.created_at))
        return list(result.all())

    async def find_for_brand_category(self, brand_id: UUID, category_id: UUID):
        return await self.db.scalar(select(BrandCategoryPolicy).where(BrandCategoryPolicy.brand_id == brand_id, BrandCategoryPolicy.category_id == category_id))

    async def find_for_brand(self, policy_id: UUID, brand_id: UUID):
        return await self.db.scalar(select(BrandCategoryPolicy).where(BrandCategoryPolicy.id == policy_id, BrandCategoryPolicy.brand_id == brand_id))
