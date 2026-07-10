import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.ids import new_uuid


class SummaryStatus(str, enum.Enum):
    validated = "validated"
    degraded = "degraded"


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    standup_date: Mapped[date] = mapped_column(Date, nullable=False)
    plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    rendered_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SummaryStatus] = mapped_column(
        Enum(SummaryStatus, name="summary_status", native_enum=False),
        nullable=False,
    )
    model_meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
