import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.update import UpdateRead, UpdateUpsert, UpdatesListResponse

router = APIRouter()


@router.put("/updates/{member_id}", response_model=UpdateRead)
async def upsert_update(
    member_id: uuid.UUID,
    body: UpdateUpsert,
    db: AsyncSession = Depends(get_db),
) -> UpdateRead:
    """Upsert today's standup update for a member. Implementation in Phase 2."""
    raise NotImplementedError("Update upsert will be implemented in the next phase.")


@router.get("/updates", response_model=UpdatesListResponse)
async def list_updates(
    standup_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> UpdatesListResponse:
    """List all updates for a date (default today). Implementation in Phase 2."""
    raise NotImplementedError("Update listing will be implemented in the next phase.")
