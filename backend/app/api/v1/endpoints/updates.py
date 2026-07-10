import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.update import UpdateRead, UpdateUpsert, UpdatesListResponse
from app.services.update_service import UpdateService

router = APIRouter()


@router.get("/updates/{member_id}", response_model=UpdateRead)
async def get_member_update(
    member_id: uuid.UUID,
    standup_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> UpdateRead:
    """Get a member's standup update for today (or a given date) to pre-fill the edit form."""
    return await UpdateService(db).get_member_update(member_id, standup_date)


@router.post("/updates/{member_id}", response_model=UpdateRead)
async def submit_update(
    member_id: uuid.UUID,
    body: UpdateUpsert,
    standup_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> UpdateRead:
    """Submit or edit a member's standup for a date (creates or updates the same row)."""
    return await UpdateService(db).upsert_update(member_id, body, standup_date)


@router.put("/updates/{member_id}", response_model=UpdateRead)
async def upsert_update(
    member_id: uuid.UUID,
    body: UpdateUpsert,
    standup_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> UpdateRead:
    """Alias for POST — submit or edit a member's standup for a date."""
    return await UpdateService(db).upsert_update(member_id, body, standup_date)


@router.get("/updates", response_model=UpdatesListResponse)
async def list_updates(
    standup_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> UpdatesListResponse:
    return await UpdateService(db).list_updates(standup_date)
