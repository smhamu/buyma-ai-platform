import asyncio
import getpass

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User


async def create_admin() -> None:
    email = input("Admin email: ").strip().lower()
    username = input("Admin username: ").strip()
    password = getpass.getpass("Admin password (12-72 characters): ")

    if not email or not username:
        raise SystemExit("Email and username are required.")
    if not 12 <= len(password) <= 72:
        raise SystemExit("Password must be 12-72 characters.")

    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(User).where(User.email == email))
        if existing is not None:
            raise SystemExit("A user with that email already exists.")

        session.add(
            User(
                email=email,
                username=username,
                hashed_password=hash_password(password),
                role="admin",
                is_active=True,
            )
        )
        await session.commit()

    print("Admin user created.")


if __name__ == "__main__":
    asyncio.run(create_admin())
