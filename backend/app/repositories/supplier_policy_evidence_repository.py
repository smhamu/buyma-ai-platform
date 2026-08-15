from datetime import datetime
from uuid import UUID

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier_policy_evidence import SupplierPolicyEvidence
from app.repositories.base_repository import BaseRepository


class SupplierPolicyEvidenceRepository(BaseRepository[SupplierPolicyEvidence]):
    SORT_COLUMNS = {
        "checked_at": SupplierPolicyEvidence.checked_at,
        "created_at": SupplierPolicyEvidence.created_at,
        "evidence_type": SupplierPolicyEvidence.evidence_type,
    }

    def __init__(self, db: AsyncSession):
        super().__init__(db, SupplierPolicyEvidence)

    async def find_for_supplier(self, evidence_id: UUID, supplier_id: UUID):
        return await self.db.scalar(
            select(SupplierPolicyEvidence).where(
                SupplierPolicyEvidence.id == evidence_id,
                SupplierPolicyEvidence.supplier_id == supplier_id,
            )
        )

    async def list_filtered(
        self, *, supplier_id: UUID, evidence_type: str | None, result: str | None,
        checked_from: datetime | None, checked_to: datetime | None, q: str | None,
        page: int, page_size: int, sort_by: str, sort_order: str,
    ) -> dict:
        filters = [SupplierPolicyEvidence.supplier_id == supplier_id]
        if evidence_type:
            filters.append(SupplierPolicyEvidence.evidence_type == evidence_type)
        if result:
            filters.append(SupplierPolicyEvidence.result == result)
        if checked_from:
            filters.append(SupplierPolicyEvidence.checked_at >= checked_from)
        if checked_to:
            filters.append(SupplierPolicyEvidence.checked_at <= checked_to)
        if q:
            term = f"%{q.strip()}%"
            filters.append(or_(SupplierPolicyEvidence.evidence_notes.ilike(term), SupplierPolicyEvidence.source_title.ilike(term), SupplierPolicyEvidence.source_url.ilike(term)))
        total = int((await self.db.scalar(select(func.count(SupplierPolicyEvidence.id)).where(*filters))) or 0)
        column = self.SORT_COLUMNS[sort_by]
        order = asc(column) if sort_order == "asc" else desc(column)
        rows = await self.db.execute(
            select(SupplierPolicyEvidence).where(*filters).order_by(order, SupplierPolicyEvidence.id.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        return {"items": list(rows.scalars().all()), "total": total}

    async def latest_by_type(self, supplier_id: UUID) -> dict[str, SupplierPolicyEvidence]:
        rows = await self.db.execute(
            select(SupplierPolicyEvidence)
            .where(SupplierPolicyEvidence.supplier_id == supplier_id)
            .order_by(SupplierPolicyEvidence.evidence_type, SupplierPolicyEvidence.checked_at.desc(), SupplierPolicyEvidence.created_at.desc())
        )
        latest = {}
        for item in rows.scalars().all():
            latest.setdefault(item.evidence_type, item)
        return latest
