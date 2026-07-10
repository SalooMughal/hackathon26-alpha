import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime


class TeamResponse(BaseModel):
    members: list[MemberRead]
