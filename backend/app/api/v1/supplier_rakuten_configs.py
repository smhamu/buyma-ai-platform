from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.common.exceptions import AppException
from app.common.responses import success_response
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.notifications.secret_store import (
    NotificationSecretStore,
    SecretStoreUnavailableError,
    get_notification_secret_store,
    rakuten_product_search_token_reference,
)
from app.schemas.supplier_rakuten_config import (
    RakutenPreviewRequest,
    SupplierRakutenConfigResponse,
    SupplierRakutenConfigUpdate,
)
from app.services.supplier_rakuten_config_service import SupplierRakutenConfigService
from app.services.supplier_rakuten_preview_service import SupplierRakutenPreviewService

router = APIRouter(prefix="/suppliers", tags=["Supplier Rakuten Configuration"])


def get_service(db: AsyncSession = Depends(get_db)) -> SupplierRakutenConfigService:
    return SupplierRakutenConfigService(db)


def response(config, supplier, *, token_configured: bool) -> SupplierRakutenConfigResponse:
    can_sync, blocked_reasons = SupplierRakutenConfigService.gate(
        config, supplier, token_configured=token_configured
    )
    can_preview, preview_blocked_reasons = SupplierRakutenConfigService.preview_gate(
        config, supplier, token_configured=token_configured
    )
    values = {
        "configured": config is not None,
        "supplier_id": supplier.id,
        "can_sync": can_sync,
        "blocked_reasons": blocked_reasons,
        "can_preview": can_preview,
        "preview_blocked_reasons": preview_blocked_reasons,
    }
    if config is not None:
        values.update({
            key: getattr(config, key)
            for key in (
                "id", "advertiser_mid", "approval_status", "sync_enabled", "search_keyword",
                "language", "max_results", "max_pages", "sync_interval_minutes", "approved_at",
                "created_at", "updated_at",
            )
        })
    return SupplierRakutenConfigResponse(**values)


async def token_exists(secret_store: NotificationSecretStore) -> bool:
    try:
        return await secret_store.exists(rakuten_product_search_token_reference(settings.app_env))
    except SecretStoreUnavailableError as exc:
        raise AppException(status.HTTP_503_SERVICE_UNAVAILABLE, "SECRET_STORE_UNAVAILABLE", str(exc))


@router.get("/{supplier_id}/rakuten-config")
async def get_rakuten_config(
    supplier_id: UUID,
    service: SupplierRakutenConfigService = Depends(get_service),
    _: User = Depends(require_admin),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    supplier = await service.require_mytheresa_supplier(supplier_id)
    config = await service.get(supplier_id)
    return success_response(
        data=response(config, supplier, token_configured=await token_exists(secret_store)),
        message="Supplier Rakuten configuration fetched successfully.",
    )


@router.put("/{supplier_id}/rakuten-config")
async def put_rakuten_config(
    supplier_id: UUID,
    payload: SupplierRakutenConfigUpdate,
    service: SupplierRakutenConfigService = Depends(get_service),
    _: User = Depends(require_admin),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    configured = await token_exists(secret_store)
    config = await service.upsert(supplier_id, payload, token_configured=configured)
    supplier = await service.require_mytheresa_supplier(supplier_id)
    return success_response(
        data=response(config, supplier, token_configured=configured),
        message="Supplier Rakuten configuration saved successfully.",
    )


@router.delete("/{supplier_id}/rakuten-config")
async def delete_rakuten_config(
    supplier_id: UUID,
    service: SupplierRakutenConfigService = Depends(get_service),
    _: User = Depends(require_admin),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    supplier = await service.require_mytheresa_supplier(supplier_id)
    await service.delete(supplier_id)
    return success_response(
        data=response(None, supplier, token_configured=await token_exists(secret_store)),
        message="Supplier Rakuten configuration removed successfully.",
    )


@router.post("/{supplier_id}/rakuten-preview")
async def preview_rakuten_products(
    supplier_id: UUID,
    payload: RakutenPreviewRequest,
    service: SupplierRakutenConfigService = Depends(get_service),
    _: User = Depends(require_admin),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    preview_service = SupplierRakutenPreviewService(
        service,
        secret_store,
        rakuten_product_search_token_reference(settings.app_env),
    )
    preview = await preview_service.preview(supplier_id, payload.page_number)
    return success_response(
        data=preview,
        message="Rakuten product preview fetched without persistence.",
    )
