from uuid import UUID

from app.common.exceptions import AppException, NotFoundException
from app.repositories.brand_repository import BrandRepository


class BrandService:
    def __init__(self, repository: BrandRepository):
        self.repository = repository

    async def get(self, brand_id: UUID):
        brand = await self.repository.find_by_id(brand_id)
        if brand is None:
            raise NotFoundException("Brand")
        return brand

    async def create(self, values: dict):
        if await self.repository.find_by_code(values["brand_code"]):
            raise AppException(409, "DUPLICATE_BRAND_CODE", "The brand code already exists.")
        return await self.repository.create(values)

    async def delete(self, brand_id: UUID) -> None:
        brand = await self.get(brand_id)
        if await self.repository.candidate_reference_count(brand_id):
            raise AppException(409, "BRAND_IN_USE", "The brand is referenced by product research candidates; deactivate it instead.")
        await self.repository.delete(brand)
