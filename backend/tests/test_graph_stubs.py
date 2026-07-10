import pytest

from app.agents.graph import build_graph


@pytest.mark.skip(reason="Full graph edge logic — implement in Phase 2")
def test_graph_compiles() -> None:
    graph = build_graph()
    assert graph is not None


@pytest.mark.skip(reason="Happy path routing — implement in Phase 2")
async def test_graph_happy_path_validated() -> None:
    pass


@pytest.mark.skip(reason="Parser failure revision loop — implement in Phase 2")
async def test_graph_parser_failure_revisions() -> None:
    pass


@pytest.mark.skip(reason="Revision cap degraded status — implement in Phase 2")
async def test_graph_revision_cap_degraded() -> None:
    pass
