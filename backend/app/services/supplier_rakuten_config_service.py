from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select

from app.common.exceptions import AppException, NotFoundException
from app.models.supplier import Supplier
from app.models.supplier_rakuten_config import SupplierRakutenConfig
from app.schemas.supplier_rakuten_config import SupplierRakutenConfigUpdate


class SupplierRakutenConfigService:
    def __init__(self, db):
        self.db = db

    async def require_mytheresa_supplier(self, supplier_id: UUID) -> Supplier:
        supplier = await self.db.scalar(select(Supplier).where(Supplier.id == supplier_id))
        if supplier is None:
            raise NotFoundException("Supplier")
        hostname = (urlparse(supplier.website_url).hostname or "").lower().rstrip(".")
        if hostname != "mytheresa.com" and not hostname.endswith(".mytheresa.com"):
            raise AppException(
                422,
                "NOT_MYTHERESA_SUPPLIER",
                "Rakuten configuration is currently limited to Mytheresa suppliers.",
            )
        return supplier

    async def get(self, supplier_id: UUID) -> SupplierRakutenConfig | None:
        await self.require_mytheresa_supplier(supplier_id)
        return await self.db.scalar(
            select(SupplierRakutenConfig).where(SupplierRakutenConfig.supplier_id == supplier_id)
        )

    async def upsert(
        self, supplier_id: UUID, payload: SupplierRakutenConfigUpdate, *, token_configured: bool
    ) -> SupplierRakutenConfig:
        supplier = await self.require_mytheresa_supplier(supplier_id)
        if payload.sync_enabled:
            if not token_configured:
                raise AppException(
                    422,
                    "RAKUTEN_TOKEN_MISSING",
                    "A Rakuten API token is required before synchronization is enabled.",
                )
            policy_reasons = self.supplier_policy_reasons(supplier)
            if policy_reasons:
                raise AppException(
                    422, "RAKUTEN_SYNC_POLICY_BLOCKED",
                    "Supplier policy gates must be approved before synchronization is enabled.",
                )
        config = await self.db.scalar(
            select(SupplierRakutenConfig).where(SupplierRakutenConfig.supplier_id == supplier_id)
        )
        values = payload.model_dump()
        previous_status = config.approval_status if config else None
        values["approved_at"] = (
            config.approved_at if config and previous_status == "approved" else datetime.now(timezone.utc)
        ) if payload.approval_status == "approved" else None
        if config is None:
            config = SupplierRakutenConfig(supplier_id=supplier.id, **values)
            self.db.add(config)
        else:
            for key, value in values.items():
                setattr(config, key, value)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def delete(self, supplier_id: UUID) -> None:
        config = await self.get(supplier_id)
        if config is None:
            return
        await self.db.delete(config)
        await self.db.commit()

    @staticmethod
    def gate(
        config: SupplierRakutenConfig | None, supplier: Supplier, *, token_configured: bool
    ) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        if config is None:
            reasons.append("configuration_missing")
        else:
            if config.approval_status != "approved":
                reasons.append("advertiser_not_approved")
            if not config.sync_enabled:
                reasons.append("sync_disabled")
        reasons.extend(SupplierRakutenConfigService.supplier_policy_reasons(supplier))
        if not token_configured:
            reasons.append("rakuten_token_missing")
        return not reasons, reasons

    @staticmethod
    def supplier_policy_reasons(supplier: Supplier) -> list[str]:
        reasons: list[str] = []
        if not supplier.is_active:
            reasons.append("supplier_inactive")
        if not supplier.automated_fetch_enabled:
            reasons.append("automated_fetch_disabled")
        if supplier.ingestion_source_type != "official_api":
            reasons.append("official_api_not_selected")
        if not supplier.official_api_available:
            reasons.append("official_api_unavailable")
        if supplier.terms_status != "allowed":
            reasons.append("terms_not_allowed")
        return reasons

    @staticmethod
    def preview_gate(
        config: SupplierRakutenConfig | None, supplier: Supplier, *, token_configured: bool
    ) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        if config is None:
            reasons.append("configuration_missing")
        elif config.approval_status != "approved":
            reasons.append("advertiser_not_approved")
        reasons.extend(SupplierRakutenConfigService.supplier_policy_reasons(supplier))
        if not token_configured:
            reasons.append("rakuten_token_missing")
        return not reasons, reasons
