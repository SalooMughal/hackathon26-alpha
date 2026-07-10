import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.update import UpdateRead, UpdateUpsert, UpdatesListResponse
from app.services.update_service import UpdateService

router = APIRouter()


@router.post("/updates/{member_id}", response_model=UpdateRead)
async def create_update(
    member_id: uuid.UUID,
    body: UpdateUpsert,
    standup_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> UpdateRead:
    """First-time submission for a member on a standup date (409 if already submitted)."""
    return await UpdateService(db).create_update(member_id, body, standup_date)


@router.put("/updates/{member_id}", response_model=UpdateRead)
async def upsert_update(
    member_id: uuid.UUID,
    body: UpdateUpsert,
    standup_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> UpdateRead:
    """Create or edit an update for a member on a standup date."""
    return await UpdateService(db).upsert_update(member_id, body, standup_date)


@router.get("/updates", response_model=UpdatesListResponse)
async def list_updates(
    standup_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> UpdatesListResponse:
    return await UpdateService(db).list_updates(standup_date)
