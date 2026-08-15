import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.brand import Brand
from app.models.supplier import Supplier  # noqa: F401 - registers ORM relationship


LUXURY_BRANDS = (
    {"brand_code": "hermes", "brand_name": "Hermès", "luxury_tier": "ultra_luxury", "online_purchase_policy": "research_only"},
    {"brand_code": "chanel", "brand_name": "CHANEL", "luxury_tier": "ultra_luxury", "online_purchase_policy": "research_only"},
    {"brand_code": "gucci", "brand_name": "Gucci", "luxury_tier": "luxury", "online_purchase_policy": "unknown"},
    {"brand_code": "prada", "brand_name": "Prada", "luxury_tier": "luxury", "online_purchase_policy": "unknown"},
    {"brand_code": "saint_laurent", "brand_name": "Saint Laurent", "luxury_tier": "luxury", "online_purchase_policy": "unknown"},
    {"brand_code": "bottega_veneta", "brand_name": "Bottega Veneta", "luxury_tier": "luxury", "online_purchase_policy": "unknown"},
    {"brand_code": "loewe", "brand_name": "Loewe", "luxury_tier": "luxury", "online_purchase_policy": "unknown"},
    {"brand_code": "dior", "brand_name": "Dior", "luxury_tier": "luxury", "online_purchase_policy": "unknown"},
    {"brand_code": "celine", "brand_name": "Celine", "luxury_tier": "luxury", "online_purchase_policy": "unknown"},
)


async def seed_luxury_brands(session) -> int:
    codes = {row[0] for row in (await session.execute(select(Brand.brand_code))).all()}
    missing = [Brand(**item, is_research_enabled=True, is_active=True) for item in LUXURY_BRANDS if item["brand_code"] not in codes]
    session.add_all(missing)
    await session.commit()
    return len(missing)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        created = await seed_luxury_brands(session)
    print(f"Luxury brand seed completed. Created: {created}")


if __name__ == "__main__":
    asyncio.run(main())
