import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.member import Member
from app.db.models.update import Update
from app.schemas.update import UpdateRead, UpdateUpsert, UpdatesListResponse


class UpdateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upsert_update(
        self, member_id: uuid.UUID, body: UpdateUpsert, standup_date: date | None = None
    ) -> UpdateRead:
        target_date = standup_date or date.today()
        member = await self.db.get(Member, member_id)
        if not member or not member.is_active:
            raise NotFoundError(f"Member {member_id} not found or inactive")

        result = await self.db.execute(
            select(Update).where(
                Update.member_id == member_id,
                Update.standup_date == target_date,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.yesterday = body.yesterday
            row.today = body.today
            row.blockers = body.blockers
        else:
            row = Update(
                member_id=member_id,
                yesterday=body.yesterday,
                today=body.today,
                blockers=body.blockers,
                standup_date=target_date,
            )
            self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return UpdateRead(
            id=row.id,
            member_id=row.member_id,
            member_name=member.name,
            yesterday=row.yesterday,
            today=row.today,
            blockers=row.blockers,
            standup_date=row.standup_date,
            updated_at=row.updated_at,
        )

    async def list_updates(self, standup_date: date | None = None) -> UpdatesListResponse:
        target_date = standup_date or date.today()
        result = await self.db.execute(
            select(Update, Member)
            .join(Member, Member.id == Update.member_id)
            .where(Update.standup_date == target_date)
            .order_by(Member.name)
        )
        rows = result.all()
        updates = [
            UpdateRead(
                id=update.id,
                member_id=update.member_id,
                member_name=member.name,
                yesterday=update.yesterday,
                today=update.today,
                blockers=update.blockers,
                standup_date=update.standup_date,
                updated_at=update.updated_at,
            )
            for update, member in rows
        ]
        return UpdatesListResponse(standup_date=target_date, updates=updates)
