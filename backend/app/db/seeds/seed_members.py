"""Idempotent member seeder — safe to run repeatedly."""

import asyncio

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.member import Member
from app.db.session import async_session_factory

TEAM_MEMBERS = ["Shahryar", "Sabir", "Asad", "Zaha"]


async def seed_members(session: AsyncSession) -> None:
    for name in TEAM_MEMBERS:
        stmt = (
            pg_insert(Member)
            .values(name=name, is_active=True)
            .on_conflict_do_nothing(index_elements=["name"])
        )
        await session.execute(stmt)


async def main() -> None:
    async with async_session_factory() as session:
        await seed_members(session)
        await session.commit()
        result = await session.execute(
            select(Member).where(Member.is_active.is_(True)).order_by(Member.name)
        )
        members = result.scalars().all()
        print(f"Seeded {len(members)} active members: {[m.name for m in members]}")


if __name__ == "__main__":
    asyncio.run(main())
