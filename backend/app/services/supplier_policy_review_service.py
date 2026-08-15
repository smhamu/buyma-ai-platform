from datetime import datetime, timezone
from math import ceil

from sqlalchemy import select

from app.models.supplier import Supplier
from app.models.supplier_policy_review_setting import SupplierPolicyReviewSetting
from app.schemas.supplier_policy_review import SupplierPolicyReviewSettingsUpdate
from app.services.supplier_policy_evidence_service import SupplierPolicyEvidenceService

REVIEW_TYPES = ("terms", "robots", "vat", "shipping", "official_api", "buyma")
STATUS_PRIORITY = {"inconsistent": 0, "review_due": 1, "no_evidence": 2, "up_to_date": 3}


class SupplierPolicyReviewService:
    def __init__(self, db, evidence_service):
        self.db = db
        self.evidence_service = evidence_service

    async def settings(self, user_id):
        row = await self.db.scalar(select(SupplierPolicyReviewSetting).where(SupplierPolicyReviewSetting.user_id == user_id))
        if row:
            return row
        defaults = SupplierPolicyReviewSettingsUpdate()
        return SupplierPolicyReviewSetting(user_id=user_id, **defaults.model_dump())

    async def update_settings(self, user_id, payload):
        row = await self.db.scalar(select(SupplierPolicyReviewSetting).where(SupplierPolicyReviewSetting.user_id == user_id))
        if row is None:
            row = SupplierPolicyReviewSetting(user_id=user_id, **payload.model_dump())
            self.db.add(row)
        else:
            for key, value in payload.model_dump().items():
                setattr(row, key, value)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def evaluate(self, supplier, settings):
        latest = await self.evidence_service.repository.latest_by_type(supplier.id)
        now = datetime.now(timezone.utc)
        required = set(settings.required_evidence_types)
        types = {}
        for evidence_type in REVIEW_TYPES:
            evidence = latest.get(evidence_type)
            current = str(self.evidence_service.current_value(supplier, evidence_type))
            age = (now - evidence.checked_at).days if evidence else None
            threshold = getattr(settings, f"{evidence_type}_max_age_days")
            consistent = current == evidence.result if evidence else None
            stale = age > threshold if age is not None and threshold is not None else None
            if evidence is None:
                status = "no_evidence" if evidence_type in required else "up_to_date"
            elif not consistent:
                status = "inconsistent"
            elif stale:
                status = "review_due"
            else:
                status = "up_to_date"
            types[evidence_type] = {
                "current": current, "latest_evidence": evidence.result if evidence else None,
                "checked_at": evidence.checked_at if evidence else None, "age_days": age,
                "max_age_days": threshold, "consistent": consistent, "is_stale": stale,
                "review_status": status,
            }
        overall = min((item["review_status"] for item in types.values()), key=STATUS_PRIORITY.get)
        issues = [key for key, value in types.items() if value["review_status"] != "up_to_date"]
        priority = "critical" if overall == "inconsistent" else "high" if any(x in issues for x in ("terms", "buyma")) else "medium" if overall != "up_to_date" else "normal"
        checked = [value["checked_at"] for value in types.values() if value["checked_at"]]
        return {
            "supplier_id": supplier.id, "supplier_name": supplier.name,
            "country_code": supplier.country_code, "supplier_type": supplier.supplier_type,
            "brand_names": [brand.brand_name for brand in supplier.brands], "updated_at": supplier.updated_at,
            "overall_status": overall, "priority": priority, "issue_types": issues,
            "oldest_evidence_at": min(checked) if checked else None, "types": types,
        }

    async def queue(self, current_user, **filters):
        owner_filter = [] if current_user.role == "admin" else [Supplier.owner_user_id == current_user.id]
        suppliers = list((await self.db.execute(select(Supplier).where(*owner_filter).order_by(Supplier.created_at.desc()))).scalars().unique())
        settings = await self.settings(current_user.id)
        items = [await self.evaluate(supplier, settings) for supplier in suppliers]
        status, country, supplier_type, brand, q, evidence_type = (filters.get(k) for k in ("overall_status", "country", "supplier_type", "brand", "q", "evidence_type"))
        if status: items = [x for x in items if x["overall_status"] == status]
        if country: items = [x for x in items if x["country_code"] == country]
        if supplier_type: items = [x for x in items if x["supplier_type"] == supplier_type]
        if brand: items = [x for x in items if any(b.lower() == brand.lower() for b in x["brand_names"])]
        if q: items = [x for x in items if q.lower() in x["supplier_name"].lower()]
        if evidence_type: items = [x for x in items if evidence_type in x["issue_types"]]
        sort = filters.get("sort", "review_priority")
        if sort == "supplier_name": items.sort(key=lambda x: x["supplier_name"].lower())
        elif sort == "oldest_evidence": items.sort(key=lambda x: x["oldest_evidence_at"] or datetime.min.replace(tzinfo=timezone.utc))
        elif sort == "updated_at": items.sort(key=lambda x: x["updated_at"], reverse=True)
        else: items.sort(key=lambda x: (STATUS_PRIORITY[x["overall_status"]], x["supplier_name"].lower()))
        summary = {key: sum(x["overall_status"] == key for x in items) for key in STATUS_PRIORITY}
        total, page, page_size = len(items), filters["page"], filters["page_size"]
        return {"items": items[(page-1)*page_size:page*page_size], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total/page_size) if total else 0, "summary": summary}
