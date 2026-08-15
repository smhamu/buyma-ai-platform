from decimal import Decimal
from uuid import UUID

from app.common.exceptions import AppException, NotFoundException
from app.repositories.product_research_repository import ProductResearchRepository
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.brand_repository import BrandRepository
from app.services.price_calculation_service import PriceCalculationService


class ProductResearchService:
    CALCULATION_FIELDS = (
        "supplier_price", "vat_policy", "vat_rate", "exchange_rate", "japan_shipping_cost",
        "estimated_import_cost", "estimated_other_cost", "buyma_price", "buyma_fee_rate",
    )

    def __init__(self, repository: ProductResearchRepository, supplier_repository: SupplierRepository, brand_repository: BrandRepository | None = None):
        self.repository = repository
        self.supplier_repository = supplier_repository
        self.brand_repository = brand_repository

    async def require_access(self, candidate_id: UUID, owner_user_id: UUID, is_admin: bool = False):
        candidate = (
            await self.repository.find_by_id(candidate_id)
            if is_admin
            else await self.repository.find_by_id_and_owner(candidate_id, owner_user_id)
        )
        if candidate is None:
            raise NotFoundException("Product research candidate")
        return candidate

    async def validate_supplier(self, supplier_id: UUID, owner_user_id: UUID, is_admin: bool = False):
        supplier = (
            await self.supplier_repository.find_by_id(supplier_id)
            if is_admin
            else await self.supplier_repository.find_by_id_and_owner(supplier_id, owner_user_id)
        )
        if supplier is None:
            raise NotFoundException("Supplier")
        return supplier

    async def validate_brand(self, brand_id: UUID):
        brand = await self.brand_repository.find_by_id(brand_id) if self.brand_repository else None
        if brand is None:
            raise NotFoundException("Brand")
        return brand

    @staticmethod
    def calculate(values: dict):
        return PriceCalculationService.calculate(
            **{field: Decimal(str(values[field])) if values[field] is not None else None
               for field in ProductResearchService.CALCULATION_FIELDS}
        )

    @staticmethod
    def apply_calculation(values: dict) -> dict:
        calculation = ProductResearchService.calculate(values)
        values.update(
            export_price=calculation.export_price,
            supplier_cost_jpy=calculation.supplier_cost_jpy,
            total_cost=calculation.total_cost,
            buyma_fee=calculation.buyma_fee,
            profit_amount=calculation.profit_amount,
            profit_rate=calculation.profit_rate,
        )
        return values

    @staticmethod
    def validate_listing_status(supplier, brand, research_status: str, *, online_purchase_available: bool = True, availability_status: str = "unknown") -> None:
        if research_status != "ready_for_listing":
            return
        if supplier.buyma_allowed_status == "prohibited":
            raise AppException(409, "SUPPLIER_PROHIBITED", "The supplier is prohibited for BUYMA purchasing.")
        if not supplier.ships_to_japan:
            raise AppException(409, "SUPPLIER_DOES_NOT_SHIP_TO_JAPAN", "The supplier does not ship to Japan.")
        if not brand.is_research_enabled:
            raise AppException(409, "BRAND_RESEARCH_DISABLED", "Research is disabled for this brand.")
        if brand.online_purchase_policy == "research_only":
            raise AppException(409, "BRAND_RESEARCH_ONLY", "This brand is restricted to research only.")
        if not online_purchase_available:
            raise AppException(409, "ONLINE_PURCHASE_UNAVAILABLE", "Online purchase is unavailable.")
        if availability_status == "out_of_stock":
            raise AppException(409, "PRODUCT_OUT_OF_STOCK", "The product is out of stock.")
