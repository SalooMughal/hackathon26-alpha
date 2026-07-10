import ssl
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Neon adds these; asyncpg uses connect_args SSL instead.
_STRIP_QUERY_KEYS = frozenset({"sslmode", "channel_binding"})


def normalize_database_url(url: str) -> str:
    """Normalize Neon/pasted URLs for asyncpg + SQLAlchemy async."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in _STRIP_QUERY_KEYS
    ]
    return urlunparse(parsed._replace(query=urlencode(query)))


def connect_args(database_url: str) -> dict:
    """asyncpg SSL via connect_args (never sslmode in the URL)."""
    if database_url.startswith("postgresql+asyncpg://"):
        ctx = ssl.create_default_context()
        return {"ssl": ctx}
    return {}
