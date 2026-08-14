from uuid import UUID

from app.common.exceptions import NotFoundException
from app.repositories.supplier_repository import SupplierRepository


class SupplierService:
    def __init__(self, repository: SupplierRepository):
        self.repository = repository

    async def require_access(self, supplier_id: UUID, owner_user_id: UUID, is_admin: bool = False):
        supplier = (
            await self.repository.find_by_id(supplier_id)
            if is_admin
            else await self.repository.find_by_id_and_owner(supplier_id, owner_user_id)
        )
        if supplier is None:
            raise NotFoundException("Supplier")
        return supplier
