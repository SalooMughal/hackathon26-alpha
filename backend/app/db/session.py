import ssl

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


def _connect_args(database_url: str) -> dict:
    """asyncpg needs SSL via connect_args (never `sslmode` in the URL).

    SQLite (used in tests) takes no SSL args.
    """
    if database_url.startswith("postgresql+asyncpg://"):
        ctx = ssl.create_default_context()
        return {"ssl": ctx}
    return {}


def create_engine() -> AsyncEngine:
    settings = get_settings()
    url = settings.DATABASE_URL
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("postgresql+asyncpg://"):
        # Tuned for serverless Postgres (Neon).
        kwargs.update(pool_size=5, max_overflow=5, pool_recycle=300)
    return create_async_engine(url, connect_args=_connect_args(url), **kwargs)


engine: AsyncEngine = create_engine()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
