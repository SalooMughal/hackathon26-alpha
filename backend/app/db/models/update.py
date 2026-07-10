import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.ids import new_uuid


class Update(Base):
    __tablename__ = "updates"
    __table_args__ = (
        UniqueConstraint("member_id", "standup_date", name="uq_updates_member_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("members.id"), nullable=False
    )
    yesterday: Mapped[str] = mapped_column(Text, nullable=False)
    today: Mapped[str] = mapped_column(Text, nullable=False)
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)
    standup_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
