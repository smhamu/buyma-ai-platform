import csv
import io
from decimal import Decimal, InvalidOperation
from uuid import UUID

from app.common.exceptions import AppException, NotFoundException
from app.repositories.brand_repository import BrandRepository
from app.repositories.product_research_repository import ProductResearchRepository
from app.repositories.research_ingestion_repository import ResearchIngestionRepository
from app.repositories.supplier_repository import SupplierRepository
from app.services.product_research_service import ProductResearchService
from app.utils.research_url import normalize_research_url, validate_supplier_domain


class ResearchIngestionService:
    def __init__(self, repository: ResearchIngestionRepository, suppliers: SupplierRepository, brands: BrandRepository, candidates: ProductResearchRepository, categories=None):
        self.repository, self.suppliers, self.brands, self.candidates, self.categories = repository, suppliers, brands, candidates, categories

    async def require_access(self, source_id: UUID, owner_id: UUID, is_admin: bool):
        source = await self.repository.find_accessible(source_id, owner_id, is_admin)
        if source is None: raise NotFoundException("Research ingestion")
        return source

    async def register_url(self, supplier_id: UUID, url: str, owner_id: UUID, is_admin: bool = False, category_id: UUID | None = None, purchase_restriction: str | None = "unknown"):
        supplier = await (self.suppliers.find_by_id(supplier_id) if is_admin else self.suppliers.find_by_id_and_owner(supplier_id, owner_id))
        if supplier is None: raise NotFoundException("Supplier")
        normalized = normalize_research_url(url)
        validate_supplier_domain(normalized, supplier.website_url)
        duplicate = await self.repository.find_duplicate(supplier.id, normalized)
        if duplicate: raise AppException(409, "DUPLICATE_SOURCE_PRODUCT", "This supplier product URL is already registered.")
        if category_id is not None and (self.categories is None or await self.categories.find_by_id(category_id) is None):
            raise NotFoundException("Product category")
        return await self.repository.create({"owner_user_id": owner_id, "supplier_id": supplier.id, "category_id": category_id, "purchase_restriction": purchase_restriction or "unknown", "source_type": "url_manual", "source_url": url, "normalized_source_url": normalized, "processing_status": "pending"})

    async def import_csv(self, content: bytes, owner_id: UUID, is_admin: bool = False):
        if len(content) > 2_000_000: raise AppException(413, "CSV_TOO_LARGE", "CSV files are limited to 2 MB.")
        try: reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
        except UnicodeDecodeError as exc: raise AppException(422, "INVALID_CSV", "CSV must be UTF-8 encoded.") from exc
        required = {"supplier", "brand", "product_url", "product_name", "supplier_product_code", "supplier_price", "currency", "availability"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames): raise AppException(422, "INVALID_CSV_COLUMNS", "CSV is missing required columns.")
        results = []
        for number, row in enumerate(reader, 2):
            try:
                supplier = await self.suppliers.find_by_name(row["supplier"], None if is_admin else owner_id)
                brand = await self.brands.find_by_name(row["brand"])
                if not supplier: raise NotFoundException("Supplier")
                if not brand: raise NotFoundException("Brand")
                if brand.id not in {item.id for item in supplier.brands}:
                    raise AppException(422, "BRAND_NOT_OFFERED_BY_SUPPLIER", "Brand is not linked to the supplier.")
                normalized = normalize_research_url(row["product_url"])
                validate_supplier_domain(normalized, supplier.website_url)
                price = Decimal(row["supplier_price"])
                if price <= 0: raise InvalidOperation
                currency = row["currency"].upper()
                if currency not in {"EUR", "JPY", "GBP", "CHF", "USD"}: raise ValueError
                availability = row["availability"]
                if availability not in {"unknown", "in_stock", "out_of_stock", "preorder"}: raise ValueError
                restriction = (row.get("purchase_restriction") or "unknown").strip()
                if restriction not in {"normal", "pre_order", "personalized", "made_to_order", "client_advisor_only", "boutique_only", "research_only", "unknown"}: raise ValueError
                if await self.repository.find_duplicate(supplier.id, normalized, row.get("supplier_product_code") or None):
                    results.append({"row": number, "status": "duplicate", "message": "Already registered."}); continue
                category = None
                category_code = (row.get("category_code") or "").strip()
                if category_code:
                    category = await self.categories.find_by_code(category_code) if self.categories else None
                    if category is None: raise AppException(422, "INVALID_CATEGORY", "Unknown category code.")
                source = await self.repository.create({"owner_user_id": owner_id, "supplier_id": supplier.id, "brand_id": brand.id, "category_id": category.id if category else None, "purchase_restriction": restriction, "source_type": "csv", "source_url": row["product_url"], "normalized_source_url": normalized, "external_product_id": row.get("supplier_product_code") or None, "raw_title": row["product_name"], "raw_brand": row["brand"], "raw_price": price, "raw_currency": currency, "raw_availability": availability, "normalized_title": row["product_name"].strip(), "normalized_price": price, "normalized_currency": currency, "normalized_availability": availability, "processing_status": "matched"})
                results.append({"row": number, "status": "success", "source_id": source.id})
            except Exception as exc:
                await self.repository.db.rollback()
                results.append({"row": number, "status": "failed", "message": getattr(exc, "detail", {}).get("message", "Invalid row.") if isinstance(getattr(exc, "detail", None), dict) else "Invalid row."})
        return results

    async def create_candidate(self, source, payload, owner_id: UUID, is_admin: bool):
        if source.candidate_id: raise AppException(409, "SOURCE_ALREADY_CONVERTED", "A candidate already exists for this source.")
        if not source.brand_id or not source.normalized_title or source.normalized_price is None or not source.normalized_currency:
            raise AppException(422, "SOURCE_NOT_READY", "The source must be normalized and matched before conversion.")
        supplier = await (self.suppliers.find_by_id(source.supplier_id) if is_admin else self.suppliers.find_by_id_and_owner(source.supplier_id, owner_id))
        if not supplier: raise NotFoundException("Supplier")
        values = {"owner_user_id": owner_id, "source_product_id": source.id, "supplier_id": supplier.id, "brand_id": source.brand_id, "category_id": source.category_id, "supplier_product_url": source.source_url, "supplier_product_code": source.external_product_id, "product_name": source.normalized_title, "supplier_price": source.normalized_price, "supplier_currency": source.normalized_currency, "vat_policy": supplier.vat_policy, "vat_rate": supplier.vat_rate, "japan_shipping_cost": payload.japan_shipping_cost if payload.japan_shipping_cost is not None else (supplier.japan_shipping_cost or 0), "exchange_rate": payload.exchange_rate, "estimated_import_cost": payload.estimated_import_cost, "estimated_other_cost": payload.estimated_other_cost, "buyma_price": payload.buyma_price, "buyma_fee_rate": payload.buyma_fee_rate, "availability_status": source.normalized_availability or "unknown", "purchase_restriction": source.purchase_restriction or "unknown", "research_status": "discovered", "online_purchase_available": True, "is_active": True}
        values = ProductResearchService.apply_calculation(values)
        candidate = await self.candidates.create(values)
        source.candidate_id, source.processing_status = candidate.id, "candidate_created"
        await self.repository.db.commit(); await self.repository.db.refresh(source)
        return candidate

    @staticmethod
    def automatic_fetch_allowed(supplier) -> bool:
        return bool(supplier.is_active and supplier.automated_fetch_enabled and supplier.ingestion_source_type in {"official_api", "structured_data", "html_parser"} and supplier.terms_status != "prohibited" and supplier.robots_status != "disallowed")
