from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# Import models so Base.metadata is fully populated for Alembic autogenerate.
from app.db.models.member import Member  # noqa: E402,F401
from app.db.models.update import Update  # noqa: E402,F401
from app.db.models.summary import Summary  # noqa: E402,F401
