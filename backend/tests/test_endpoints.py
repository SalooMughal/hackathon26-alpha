import pytest

from app.db.models.member import Member

SAMPLE_UPDATE = {
    "yesterday": "Finished backend work.",
    "today": "Testing the API.",
    "blockers": "None",
}


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"


@pytest.mark.asyncio
async def test_team_list_after_seed(client, db_session):
    db_session.add(Member(name="Sabir", is_active=True))
    db_session.add(Member(name="Asad", is_active=True))
    await db_session.commit()

    response = await client.get("/api/v1/team")
    assert response.status_code == 200
    names = [m["name"] for m in response.json()["members"]]
    assert "Sabir" in names
    assert "Asad" in names


@pytest.mark.asyncio
async def test_update_saved_with_standup_date(client, db_session):
    member = Member(name="Sabir", is_active=True)
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    response = await client.put(
        f"/api/v1/updates/{member.id}",
        json=SAMPLE_UPDATE,
        params={"standup_date": "2026-07-10"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["standup_date"] == "2026-07-10"
    assert data["member_name"] == "Sabir"


@pytest.mark.asyncio
async def test_post_duplicate_rejected_but_other_members_allowed(client, db_session):
    sabir = Member(name="Sabir", is_active=True)
    asad = Member(name="Asad", is_active=True)
    db_session.add_all([sabir, asad])
    await db_session.commit()
    await db_session.refresh(sabir)
    await db_session.refresh(asad)

    first = await client.post(f"/api/v1/updates/{sabir.id}", json=SAMPLE_UPDATE)
    assert first.status_code == 200

    duplicate = await client.post(
        f"/api/v1/updates/{sabir.id}",
        json={
            "yesterday": "Different content.",
            "today": "Should not save on POST.",
            "blockers": "None",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_update"

    other_member = await client.post(f"/api/v1/updates/{asad.id}", json=SAMPLE_UPDATE)
    assert other_member.status_code == 200
    assert other_member.json()["member_name"] == "Asad"


@pytest.mark.asyncio
async def test_put_allows_editing_same_member(client, db_session):
    member = Member(name="Sabir", is_active=True)
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    await client.post(f"/api/v1/updates/{member.id}", json=SAMPLE_UPDATE)
    response = await client.put(
        f"/api/v1/updates/{member.id}",
        json={
            "yesterday": "Revised yesterday.",
            "today": "Revised today.",
            "blockers": "Still none",
        },
    )
    assert response.status_code == 200
    assert response.json()["yesterday"] == "Revised yesterday."
