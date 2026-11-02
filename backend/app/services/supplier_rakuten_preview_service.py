from datetime import datetime, timezone
from uuid import UUID

from app.common.exceptions import AppException
from app.notifications.secret_store import (
    SecretNotFoundError,
    SecretStoreUnavailableError,
)
from app.research_providers.rakuten import RakutenProductSearchClient
from app.schemas.supplier_rakuten_config import (
    RakutenPreviewProduct,
    RakutenPreviewResponse,
)
from app.services.supplier_rakuten_config_service import SupplierRakutenConfigService


class SupplierRakutenPreviewService:
    def __init__(self, config_service, secret_store, token_reference: str, client_factory=None):
        self.config_service = config_service
        self.secret_store = secret_store
        self.token_reference = token_reference
        self.client_factory = client_factory or RakutenProductSearchClient

    async def preview(self, supplier_id: UUID, page_number: int) -> RakutenPreviewResponse:
        supplier = await self.config_service.require_mytheresa_supplier(supplier_id)
        config = await self.config_service.get(supplier_id)
        allowed, reasons = SupplierRakutenConfigService.preview_gate(
            config, supplier, token_configured=True
        )
        if not allowed:
            raise AppException(
                409,
                "RAKUTEN_PREVIEW_BLOCKED",
                "Rakuten preview is blocked by supplier or advertiser policy settings.",
            )
        if page_number > config.max_pages:
            raise AppException(
                422,
                "RAKUTEN_PREVIEW_PAGE_LIMIT",
                "The requested preview page exceeds the configured page limit.",
            )
        try:
            token = await self.secret_store.get_secret(self.token_reference)
        except SecretNotFoundError as exc:
            raise AppException(409, "RAKUTEN_TOKEN_MISSING", "A Rakuten API token is required for preview.") from exc
        except SecretStoreUnavailableError as exc:
            raise AppException(503, "SECRET_STORE_UNAVAILABLE", "The secret store is temporarily unavailable.") from exc

        async with self.client_factory(token) as client:
            page = await client.search(
                advertiser_id=config.advertiser_mid,
                keyword=config.search_keyword,
                language=config.language,
                max_results=config.max_results,
                page_number=page_number,
            )
        return RakutenPreviewResponse(
            supplier_id=supplier.id,
            advertiser_mid=config.advertiser_mid,
            page_number=page.page_number,
            total_pages=page.total_pages,
            total_matches=page.total_matches,
            fetched_at=datetime.now(timezone.utc),
            persisted=False,
            items=[
                RakutenPreviewProduct(
                    advertiser_id=item.advertiser_id,
                    advertiser_name=item.advertiser_name,
                    link_id=item.link_id,
                    sku=item.sku,
                    name=item.name,
                    price=item.price,
                    currency=item.currency,
                    product_url=item.product_url,
                    image_url=item.image_url,
                    primary_category=item.primary_category,
                    secondary_category=item.secondary_category,
                    short_description=item.short_description,
                )
                for item in page.items
            ],
        )
