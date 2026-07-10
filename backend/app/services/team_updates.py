from app.db.models.member import Member
from app.db.models.update import Update


def partition_team_updates(
    members: list[Member],
    updates_by_member: dict,
) -> tuple[list[dict], list[str]]:
    """Split active members into submitted updates vs missing for a standup date."""
    raw_updates: list[dict] = []
    missing_members: list[str] = []

    for member in members:
        update: Update | None = updates_by_member.get(member.id)
        if (
            update is None
            or not update.yesterday.strip()
            or not update.today.strip()
        ):
            missing_members.append(member.name)
            continue
        raw_updates.append(
            {
                "name": member.name,
                "yesterday": update.yesterday,
                "today": update.today,
                "blockers": update.blockers or "",
            }
        )

    return raw_updates, missing_members
