import uuid
from datetime import date, datetime, timezone

from app.db.models.member import Member
from app.db.models.update import Update
from app.services.team_updates import partition_team_updates


def _member(name: str) -> Member:
    return Member(id=uuid.uuid4(), name=name, is_active=True)


def _update(member_id: uuid.UUID, yesterday: str, today: str) -> Update:
    now = datetime.now(timezone.utc)
    return Update(
        id=uuid.uuid4(),
        member_id=member_id,
        yesterday=yesterday,
        today=today,
        blockers="None",
        standup_date=date(2026, 7, 10),
        created_at=now,
        updated_at=now,
    )


def test_partition_team_updates_partial_submission():
    sabir = _member("Sabir")
    asad = _member("Asad")
    zaha = _member("Zaha")
    updates = {
        sabir.id: _update(sabir.id, "Built API", "Testing"),
        asad.id: _update(asad.id, "Built UI", "Polish"),
    }

    raw, missing = partition_team_updates([sabir, asad, zaha], updates)

    assert missing == ["Zaha"]
    assert len(raw) == 2
    assert {entry["name"] for entry in raw} == {"Sabir", "Asad"}


def test_partition_team_updates_treats_empty_fields_as_missing():
    sabir = _member("Sabir")
    update = _update(sabir.id, "   ", "Has today only")

    raw, missing = partition_team_updates([sabir], {sabir.id: update})

    assert missing == ["Sabir"]
    assert raw == []
