from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.member import TeamResponse

router = APIRouter()


@router.get("/team", response_model=TeamResponse)
async def list_team(db: AsyncSession = Depends(get_db)) -> TeamResponse:
    """List active team members. Implementation in Phase 2."""
    raise NotImplementedError("Team listing will be implemented in the next phase.")
