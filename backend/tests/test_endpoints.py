import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.skip(reason="Requires test DB — implement in Phase 2")
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] in ("ok", "fail")


@pytest.mark.skip(reason="Requires seeded DB — implement in Phase 2")
async def test_team_list(client: AsyncClient) -> None:
    response = await client.get("/api/v1/team")
    assert response.status_code == 200


@pytest.mark.skip(reason="Requires seeded DB — implement in Phase 2")
async def test_update_upsert(client: AsyncClient) -> None:
    pass


@pytest.mark.skip(reason="Requires full workflow — implement in Phase 2")
async def test_summary_flow(client: AsyncClient) -> None:
    pass
