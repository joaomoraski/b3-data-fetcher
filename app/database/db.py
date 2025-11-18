from typing import Any, AsyncGenerator, Optional

from sqlalchemy import NullPool, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

__async_engine: Optional[AsyncEngine] = None

engine = create_async_engine(settings.APP_POSTGRESQL_URI, poolclass=NullPool)
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

SYNC_DATABASE_URL = settings.APP_POSTGRESQL_URI.replace(
    "postgresql+asyncpg", "postgresql"
)
sync_engine = create_engine(SYNC_DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


async def get_db_session() -> AsyncGenerator[AsyncSession, Any]:
    try:
        session = session_maker()
        yield session  # Study what exactly is yield
    finally:
        await session.close()
