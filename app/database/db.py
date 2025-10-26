from typing import Any, AsyncGenerator, Optional

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings

__async_engine: Optional[AsyncEngine] = None

engine = create_async_engine(settings.APP_POSTGRESQL_URI, poolclass=NullPool)
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, Any]:
    try:
        session = session_maker()
        yield session  # Study what exactly is yield
    finally:
        await session.close()
