from uuid import UUID

from app.common.exceptions import AppException, NotFoundException


class BrandCategoryPolicyService:
    def __init__(self, brands, categories, policies):
        self.brands, self.categories, self.policies = brands, categories, policies

    async def resolve(self, brand_id: UUID, category_id: UUID | None):
        brand = await self.brands.find_by_id(brand_id)
        if brand is None:
            raise NotFoundException("Brand")
        if category_id is not None:
            category = await self.categories.find_by_id(category_id)
            if category is None or not category.is_active:
                raise NotFoundException("Product category")
            override = await self.policies.find_for_brand_category(brand_id, category_id)
            if override:
                return override.online_purchase_policy, override.research_enabled, "category_override"
        return brand.online_purchase_policy, brand.is_research_enabled, "brand_default"

    async def create(self, brand_id: UUID, values: dict):
        if await self.brands.find_by_id(brand_id) is None:
            raise NotFoundException("Brand")
        category = await self.categories.find_by_id(values["category_id"])
        if category is None:
            raise NotFoundException("Product category")
        if await self.policies.find_for_brand_category(brand_id, values["category_id"]):
            raise AppException(409, "DUPLICATE_BRAND_CATEGORY_POLICY", "A policy already exists for this brand and category.")
        return await self.policies.create({"brand_id": brand_id, **values})
