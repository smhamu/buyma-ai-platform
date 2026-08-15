import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.brand import Brand
from app.models.product_category import BrandCategoryPolicy, ProductCategory

CHANEL_POLICIES = {
    "handbags": "boutique_only",
    "small_leather_goods": "boutique_only",
    "shoes": "boutique_only",
    "fragrance": "normal",
    "beauty": "normal",
    "eyewear": "normal",
}


async def seed_chanel_category_policies(session) -> int:
    brand = await session.scalar(select(Brand).where(Brand.brand_code == "chanel"))
    if brand is None:
        raise RuntimeError("CHANEL brand is missing.")
    categories = {x.category_code: x for x in (await session.scalars(select(ProductCategory).where(ProductCategory.category_code.in_(CHANEL_POLICIES)))).all()}
    missing_codes = set(CHANEL_POLICIES) - set(categories)
    if missing_codes:
        raise RuntimeError("Required product categories are missing.")
    existing = set((await session.scalars(select(BrandCategoryPolicy.category_id).where(BrandCategoryPolicy.brand_id == brand.id))).all())
    items = [BrandCategoryPolicy(brand_id=brand.id, category_id=category.id, online_purchase_policy=CHANEL_POLICIES[code], research_enabled=True, policy_notes="Based on docs/suppliers/CHANEL_EU_RESEARCH.md; reviewed 2026-08-15.") for code, category in categories.items() if category.id not in existing]
    if not items:
        return 0
    session.add_all(items)
    await session.commit()
    return len(items)


async def main():
    async with AsyncSessionLocal() as session:
        created = await seed_chanel_category_policies(session)
    print(f"CHANEL category policy seed completed. Created: {created}")


if __name__ == "__main__":
    asyncio.run(main())
