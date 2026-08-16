from datetime import datetime, timezone
from uuid import UUID

from app.common.exceptions import NotFoundException
from app.repositories.supplier_policy_evidence_repository import SupplierPolicyEvidenceRepository
from app.services.supplier_service import SupplierService
from app.utils.research_url import normalize_research_url


POLICY_FIELDS = {
    "terms": "terms_status",
    "robots": "robots_status",
    "vat": "vat_policy",
    "shipping": "ships_to_japan",
    "official_api": "official_api_available",
    "buyma": "buyma_allowed_status",
}


class SupplierPolicyEvidenceService:
    def __init__(self, repository: SupplierPolicyEvidenceRepository, supplier_service: SupplierService, review_state_service=None):
        self.repository = repository
        self.supplier_service = supplier_service
        self.review_state_service = review_state_service

    @staticmethod
    def policy_snapshot(supplier) -> dict:
        return {
            "terms_status": supplier.terms_status,
            "robots_status": supplier.robots_status,
            "vat_policy": supplier.vat_policy,
            "ships_to_japan": supplier.ships_to_japan,
            "official_api_available": supplier.official_api_available,
            "buyma_allowed_status": supplier.buyma_allowed_status,
            "ingestion_source_type": supplier.ingestion_source_type,
            "automated_fetch_enabled": supplier.automated_fetch_enabled,
        }

    async def create(self, supplier_id: UUID, payload, current_user):
        supplier = await self.supplier_service.require_access(
            supplier_id, current_user.id, current_user.role == "admin"
        )
        values = payload.model_dump()
        if values["source_url"]:
            values["source_url"] = normalize_research_url(values["source_url"])
        values.update(
            supplier_id=supplier.id,
            owner_user_id=supplier.owner_user_id,
            checked_by_user_id=current_user.id,
            policy_snapshot=self.policy_snapshot(supplier),
        )
        if self.review_state_service is None:
            return await self.repository.create(values)
        evidence = await self.repository.create_without_commit(values)
        # Evidence, review state, transition and outbox are committed together.
        await self.review_state_service.evaluate_and_record_supplier_review(supplier.id)
        return evidence

    async def require_access(self, supplier_id: UUID, evidence_id: UUID, current_user):
        await self.supplier_service.require_access(
            supplier_id, current_user.id, current_user.role == "admin"
        )
        evidence = await self.repository.find_for_supplier(evidence_id, supplier_id)
        if evidence is None:
            raise NotFoundException("Supplier policy evidence")
        return evidence

    @staticmethod
    def current_value(supplier, evidence_type: str):
        value = getattr(supplier, POLICY_FIELDS[evidence_type])
        if evidence_type in {"shipping", "official_api"}:
            return "supported" if value else "unsupported"
        return value

    @staticmethod
    def is_review_due(checked_at: datetime, max_age_days: int) -> bool:
        return (datetime.now(timezone.utc) - checked_at).days > max_age_days

    async def summary(self, supplier_id: UUID, current_user, max_age_days: int | None = None):
        supplier = await self.supplier_service.require_access(
            supplier_id, current_user.id, current_user.role == "admin"
        )
        latest = await self.repository.latest_by_type(supplier_id)
        now = datetime.now(timezone.utc)
        summary = {}
        for evidence_type in POLICY_FIELDS:
            evidence = latest.get(evidence_type)
            current = self.current_value(supplier, evidence_type)
            age_days = (now - evidence.checked_at).days if evidence else None
            summary[evidence_type] = {
                "current": current,
                "latest_evidence": evidence.result if evidence else None,
                "evidence_id": evidence.id if evidence else None,
                "checked_at": evidence.checked_at if evidence else None,
                "age_days": age_days,
                "is_stale": age_days > max_age_days if age_days is not None and max_age_days is not None else None,
                "consistent": current == evidence.result if evidence else None,
            }
        return summary
