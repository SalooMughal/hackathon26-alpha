import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.summary import (
    SummaryCreateRequest,
    SummaryDetailResponse,
    SummaryResponse,
)
from app.services.summary_service import SummaryService

router = APIRouter()


@router.post("/summary", response_model=SummaryResponse)
async def create_summary(
    body: SummaryCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    return await SummaryService(db).generate_summary(body.standup_date)


@router.get("/summary/{summary_id}", response_model=SummaryDetailResponse)
async def get_summary(
    summary_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SummaryDetailResponse:
    return await SummaryService(db).get_summary(summary_id)
