import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.product_category import ProductCategory

PRODUCT_CATEGORIES = (
    ("handbags", "Handbags"),
    ("small_leather_goods", "Small Leather Goods"),
    ("shoes", "Shoes"),
    ("ready_to_wear", "Ready-to-wear"),
    ("accessories", "Accessories"),
    ("jewelry", "Jewelry"),
    ("watches", "Watches"),
    ("eyewear", "Eyewear"),
    ("fragrance", "Fragrance"),
    ("beauty", "Beauty"),
)


async def seed_product_categories(session) -> int:
    codes = set((await session.scalars(select(ProductCategory.category_code))).all())
    missing = [ProductCategory(category_code=code, category_name=name, is_active=True) for code, name in PRODUCT_CATEGORIES if code not in codes]
    if not missing:
        return 0
    session.add_all(missing)
    await session.commit()
    return len(missing)


async def main():
    async with AsyncSessionLocal() as session:
        created = await seed_product_categories(session)
    print(f"Product category seed completed. Created: {created}")


if __name__ == "__main__":
    asyncio.run(main())
