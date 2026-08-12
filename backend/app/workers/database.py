from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


async def create_worker_session():
    engine = create_async_engine(
        settings.database_url,
        echo=True,
        poolclass=NullPool,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    return session_factory(), engine
