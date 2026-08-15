import asyncio
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.brand import Brand
from app.models.supplier import Supplier
from app.models.user import User


PRADA_EU_SUPPLIERS = (
    {"name": "Prada Official Online Store France", "country_code": "FR", "website_url": "https://www.prada.com/fr/fr/"},
    {"name": "Prada Official Online Store Germany", "country_code": "DE", "website_url": "https://www.prada.com/de/de/"},
    {"name": "Prada Official Online Store Italy", "country_code": "IT", "website_url": "https://www.prada.com/it/it/"},
    {"name": "Prada Official Online Store Spain", "country_code": "ES", "website_url": "https://www.prada.com/es/es/"},
)

CONSERVATIVE_POLICY = {
    "supplier_type": "authorized_retailer",
    "default_currency": "EUR",
    "ships_to_japan": False,
    "vat_policy": "not_refunded",
    "vat_rate": None,
    "japan_shipping_cost": None,
    "buyma_allowed_status": "unchecked",
    "research_status": "reviewing",
    "is_active": True,
    "ingestion_source_type": "url_manual",
    "automated_fetch_enabled": False,
    "terms_status": "restricted",
    "robots_status": "restricted",
    "official_api_available": False,
    "parser_key": None,
    "request_interval_seconds": None,
    "research_policy_notes": (
        "Manual research only. Prada's EU sales terms expressly prohibit resale "
        "or transfer for commercial/professional purposes. No permission for "
        "automated collection or public product API was confirmed. The reviewed "
        "robots.txt restricts search, account and internal JSON/content paths. "
        "See docs/suppliers/PRADA_EU_RESEARCH.md."
    ),
}


async def seed_prada_eu_suppliers(session, owner_id: UUID) -> int:
    brand = await session.scalar(select(Brand).where(Brand.brand_code == "prada"))
    if brand is None:
        raise RuntimeError("Prada brand is missing. Run seed_luxury_brands.py first.")
    names = {item["name"] for item in PRADA_EU_SUPPLIERS}
    existing = await session.scalars(select(Supplier).where(Supplier.owner_user_id == owner_id, Supplier.name.in_(names)))
    existing_names = {supplier.name for supplier in existing.all()}
    missing = [Supplier(owner_user_id=owner_id, brands=[brand], notes="Initial policy researched on 2026-08-15; see docs/suppliers/PRADA_EU_RESEARCH.md.", **item, **CONSERVATIVE_POLICY) for item in PRADA_EU_SUPPLIERS if item["name"] not in existing_names]
    if not missing:
        return 0
    session.add_all(missing)
    await session.commit()
    return len(missing)


async def main() -> None:
    email = input("Owner admin email: ").strip().lower()
    if not email:
        raise SystemExit("Owner admin email is required.")
    async with AsyncSessionLocal() as session:
        owner = await session.scalar(select(User).where(User.email == email, User.role == "admin", User.is_active.is_(True)))
        if owner is None:
            raise SystemExit("An active admin with that email was not found.")
        created = await seed_prada_eu_suppliers(session, owner.id)
    print(f"Prada EU supplier seed completed. Created: {created}")


if __name__ == "__main__":
    asyncio.run(main())
