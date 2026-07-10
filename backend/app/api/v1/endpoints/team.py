from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.member import TeamResponse
from app.services.team_service import TeamService

router = APIRouter()


@router.get("/team", response_model=TeamResponse)
async def list_team(db: AsyncSession = Depends(get_db)) -> TeamResponse:
    return await TeamService(db).list_active_members()
