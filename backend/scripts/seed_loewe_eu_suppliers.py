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


LOEWE_EU_SUPPLIERS = (
    {"name": "LOEWE Official Online Store France", "country_code": "FR", "website_url": "https://www.loewe.com/eur/fr/"},
    {"name": "LOEWE Official Online Store Germany", "country_code": "DE", "website_url": "https://www.loewe.com/eur/de/"},
    {"name": "LOEWE Official Online Store Italy", "country_code": "IT", "website_url": "https://www.loewe.com/eur/it/"},
    {"name": "LOEWE Official Online Store Spain", "country_code": "ES", "website_url": "https://www.loewe.com/eur/es/"},
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
        "Manual research only. LOEWE terms prohibit resale and commercial use, "
        "while destination selection controls currency and shipping conditions. "
        "Japan appearing in the global shipping table does not confirm an EUR EU-locale "
        "checkout to Japan. robots.txt restricts commerce, search and variation routes. "
        "No public Product API or automated collection permission was confirmed. "
        "See docs/suppliers/LOEWE_EU_RESEARCH.md."
    ),
}


async def seed_loewe_eu_suppliers(session, owner_id: UUID) -> int:
    brand = await session.scalar(select(Brand).where(Brand.brand_code == "loewe"))
    if brand is None:
        raise RuntimeError("LOEWE brand is missing. Run seed_luxury_brands.py first.")
    names = {item["name"] for item in LOEWE_EU_SUPPLIERS}
    existing = await session.scalars(
        select(Supplier).where(Supplier.owner_user_id == owner_id, Supplier.name.in_(names))
    )
    existing_names = {supplier.name for supplier in existing.all()}
    missing = [
        Supplier(
            owner_user_id=owner_id,
            brands=[brand],
            notes="Initial policy researched on 2026-08-15; see docs/suppliers/LOEWE_EU_RESEARCH.md.",
            **item,
            **CONSERVATIVE_POLICY,
        )
        for item in LOEWE_EU_SUPPLIERS
        if item["name"] not in existing_names
    ]
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
        owner = await session.scalar(
            select(User).where(User.email == email, User.role == "admin", User.is_active.is_(True))
        )
        if owner is None:
            raise SystemExit("An active admin with that email was not found.")
        created = await seed_loewe_eu_suppliers(session, owner.id)
    print(f"LOEWE EU supplier seed completed. Created: {created}")


if __name__ == "__main__":
    asyncio.run(main())
