from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.connect import connect_args


def create_engine() -> AsyncEngine:
    settings = get_settings()
    url = settings.DATABASE_URL
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("postgresql+asyncpg://"):
        kwargs.update(pool_size=5, max_overflow=5, pool_recycle=300)
    return create_async_engine(url, connect_args=connect_args(url), **kwargs)


engine: AsyncEngine = create_engine()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
