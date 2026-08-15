from uuid import UUID

from app.common.exceptions import NotFoundException
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.brand_repository import BrandRepository


class SupplierService:
    def __init__(self, repository: SupplierRepository, brand_repository: BrandRepository):
        self.repository = repository
        self.brand_repository = brand_repository

    async def set_brands(self, supplier, brand_ids: list[UUID]) -> None:
        brands = await self.brand_repository.find_many_by_ids(brand_ids)
        if len(brands) != len(set(brand_ids)):
            raise NotFoundException("Brand")
        supplier.brands = brands
        await self.repository.db.commit()
        await self.repository.db.refresh(supplier)

    async def require_access(self, supplier_id: UUID, owner_user_id: UUID, is_admin: bool = False):
        supplier = (
            await self.repository.find_by_id(supplier_id)
            if is_admin
            else await self.repository.find_by_id_and_owner(supplier_id, owner_user_id)
        )
        if supplier is None:
            raise NotFoundException("Supplier")
        return supplier
