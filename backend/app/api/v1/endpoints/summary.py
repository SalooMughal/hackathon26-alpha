import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.summary import (
    SummaryCreateRequest,
    SummaryDetailResponse,
    SummaryResponse,
)

router = APIRouter()


@router.post("/summary", response_model=SummaryResponse)
async def create_summary(
    body: SummaryCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    """Run the LangGraph workflow and persist a summary. Implementation in Phase 2."""
    raise NotImplementedError("Summary generation will be implemented in the next phase.")


@router.get("/summary/{summary_id}", response_model=SummaryDetailResponse)
async def get_summary(
    summary_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SummaryDetailResponse:
    """Fetch a persisted summary by ID. Implementation in Phase 2."""
    raise NotImplementedError("Summary retrieval will be implemented in the next phase.")
