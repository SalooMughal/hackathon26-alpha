from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.member import Member
from app.schemas.member import MemberRead, TeamResponse


class TeamService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_active_members(self) -> TeamResponse:
        result = await self.db.execute(
            select(Member)
            .where(Member.is_active.is_(True))
            .order_by(Member.name)
        )
        members = result.scalars().all()
        return TeamResponse(
            members=[MemberRead.model_validate(m) for m in members]
        )
