import pytest
from httpx import ASGITransport, AsyncClient

from app.db.models.member import Member
from app.main import app


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
