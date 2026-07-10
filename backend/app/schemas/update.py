import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class UpdateUpsert(BaseModel):
    yesterday: str = Field(..., min_length=1)
    today: str = Field(..., min_length=1)
    blockers: str | None = None


class UpdateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    member_id: uuid.UUID
    member_name: str | None = None
    yesterday: str
    today: str
    blockers: str | None
    standup_date: date
    updated_at: datetime


class UpdatesListResponse(BaseModel):
    standup_date: date
    updates: list[UpdateRead]
