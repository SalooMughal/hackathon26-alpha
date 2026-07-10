import json
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.graph import build_graph, route_after_parser, route_after_validator
from app.agents.state import GraphState
from app.schemas.plan import SummaryPlan
from app.schemas.sanitized import SanitizedMember, SanitizedUpdates
from app.schemas.summary import Blocker, PersonItems, StandupSummary
from app.schemas.validation import ValidationResult


def _sanitized() -> SanitizedUpdates:
    return SanitizedUpdates(
        members=[
            SanitizedMember(
                name="Sabir",
                yesterday="Built API",
                today="Tests",
                blockers="Need key",
                was_modified=False,
            )
        ]
    )


def _plan() -> SummaryPlan:
    return SummaryPlan(
        grouping="by_section",
        section_order=["done", "doing", "blockers"],
        emphasis=["Highlight blocker"],
        tone="neutral",
        length_budget_words=120,
    )


def _summary() -> StandupSummary:
    return StandupSummary(
        tldr="Sabir blocked on key.",
        done=[PersonItems(person="Sabir", items=["Built API"])],
        doing=[PersonItems(person="Sabir", items=["Tests"])],
        blockers=[Blocker(person="Sabir", item="Need key", severity="high")],
    )


VALID_JSON = json.dumps(_summary().model_dump())


@pytest.mark.asyncio
async def test_happy_path_validated():
    graph = build_graph()

    async def fake_sanitizer(state):
        return {"sanitized_updates": _sanitized()}

    async def fake_planner(state):
        return {"plan": _plan()}

    async def fake_summarizer(state):
        return {"raw_summary_output": VALID_JSON, "parsed_summary": None, "feedback": None}

    async def fake_validator(state):
        return {
            "validation": ValidationResult(approved=True, issues=[]),
            "status": "validated",
        }

    with patch("app.agents.graph.sanitizer_node", fake_sanitizer), patch(
        "app.agents.graph.planner_node", fake_planner
    ), patch("app.agents.graph.summarizer_node", fake_summarizer), patch(
        "app.agents.graph.validator_node", fake_validator
    ):
        g = build_graph()
        final = await g.ainvoke(
            GraphState(standup_date="2026-07-10", raw_updates=[{"name": "Sabir"}]).model_dump()
        )
    assert final["status"] == "validated"


@pytest.mark.asyncio
async def test_parse_fail_then_success():
    calls = {"n": 0}

    async def fake_summarizer(state):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"raw_summary_output": "not-json", "parsed_summary": None}
        return {"raw_summary_output": VALID_JSON, "parsed_summary": None, "feedback": None}

    graph = build_graph()
    with patch("app.agents.graph.sanitizer_node", AsyncMock(return_value={"sanitized_updates": _sanitized()})), patch(
        "app.agents.graph.planner_node", AsyncMock(return_value={"plan": _plan()})
    ), patch("app.agents.graph.summarizer_node", fake_summarizer), patch(
        "app.agents.graph.validator_node",
        AsyncMock(
            return_value={
                "validation": ValidationResult(approved=True, issues=[]),
                "status": "validated",
            }
        ),
    ):
        g = build_graph()
        final = await g.ainvoke(
            GraphState(standup_date="2026-07-10", raw_updates=[{"name": "Sabir"}]).model_dump(),
            config={"recursion_limit": 15},
        )
    assert final["status"] == "validated"
    assert calls["n"] >= 2


@pytest.mark.asyncio
async def test_validator_reject_then_retry():
    calls = {"n": 0}

    async def fake_validator(state):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "validation": ValidationResult(approved=False, issues=["Missing blocker"]),
                "feedback": "- Missing blocker",
                "revision_count": state.revision_count + 1,
            }
        return {
            "validation": ValidationResult(approved=True, issues=[]),
            "status": "validated",
        }

    with patch("app.agents.graph.sanitizer_node", AsyncMock(return_value={"sanitized_updates": _sanitized()})), patch(
        "app.agents.graph.planner_node", AsyncMock(return_value={"plan": _plan()})
    ), patch(
        "app.agents.graph.summarizer_node",
        AsyncMock(return_value={"raw_summary_output": VALID_JSON, "parsed_summary": None}),
    ), patch("app.agents.graph.validator_node", fake_validator):
        g = build_graph()
        final = await g.ainvoke(
            GraphState(standup_date="2026-07-10", raw_updates=[{"name": "Sabir"}]).model_dump(),
            config={"recursion_limit": 15},
        )
    assert final["status"] == "validated"


@pytest.mark.asyncio
async def test_revision_cap_fallback():
    async def fake_summarizer(state):
        return {"raw_summary_output": "broken", "parsed_summary": None}

    concise = StandupSummary(
        tldr="Sabir is blocked on API key.",
        done=[PersonItems(person="Sabir", items=["Built FastAPI routes"])],
        doing=[PersonItems(person="Sabir", items=["Testing summary endpoint"])],
        blockers=[Blocker(person="Sabir", item="Need key", severity="high")],
    )

    async def fake_compress(state):
        return {
            "parsed_summary": concise,
            "validation": ValidationResult(approved=True, issues=[]),
            "status": "validated",
        }

    with patch("app.agents.graph.sanitizer_node", AsyncMock(return_value={"sanitized_updates": _sanitized()})), patch(
        "app.agents.graph.planner_node", AsyncMock(return_value={"plan": _plan()})
    ), patch("app.agents.graph.summarizer_node", fake_summarizer), patch(
        "app.agents.graph.compressor_node", fake_compress
    ):
        g = build_graph()
        final = await g.ainvoke(
            GraphState(standup_date="2026-07-10", raw_updates=[{"name": "Sabir"}]).model_dump(),
            config={"recursion_limit": 15},
        )
    assert final["status"] == "validated"
    assert final["parsed_summary"]["tldr"] == "Sabir is blocked on API key."


@pytest.mark.asyncio
async def test_planner_exception_fallback():
    async def fake_planner(state):
        return {"status": "degraded", "error": "planner: boom"}

    concise = _summary()

    async def fake_compress(state):
        return {
            "parsed_summary": concise,
            "validation": ValidationResult(approved=True, issues=[]),
            "status": "validated",
        }

    with patch("app.agents.graph.sanitizer_node", AsyncMock(return_value={"sanitized_updates": _sanitized()})), patch(
        "app.agents.graph.planner_node", fake_planner
    ), patch("app.agents.graph.compressor_node", fake_compress):
        g = build_graph()
        final = await g.ainvoke(
            GraphState(standup_date="2026-07-10", raw_updates=[{"name": "Sabir"}]).model_dump(),
            config={"recursion_limit": 15},
        )
    assert final["status"] == "validated"


@pytest.mark.asyncio
async def test_sanitizer_fail_open():
    async def fake_sanitizer(state):
        return {"sanitized_updates": _sanitized()}

    with patch("app.agents.graph.sanitizer_node", fake_sanitizer), patch(
        "app.agents.graph.planner_node", AsyncMock(return_value={"plan": _plan()})
    ), patch(
        "app.agents.graph.summarizer_node",
        AsyncMock(return_value={"raw_summary_output": VALID_JSON, "parsed_summary": None}),
    ), patch(
        "app.agents.graph.validator_node",
        AsyncMock(
            return_value={
                "validation": ValidationResult(approved=True, issues=[]),
                "status": "validated",
            }
        ),
    ):
        g = build_graph()
        final = await g.ainvoke(
            GraphState(standup_date="2026-07-10", raw_updates=[{"name": "Sabir"}]).model_dump()
        )
    assert final["status"] == "validated"


def test_route_after_parser_degraded():
    state = GraphState(
        standup_date="2026-07-10",
        raw_updates=[],
        status="degraded",
    )
    assert route_after_parser(state) == "compress"


def test_route_after_validator_compress_when_revisions_exhausted():
    state = GraphState(
        standup_date="2026-07-10",
        raw_updates=[],
        revision_count=99,
        parsed_summary=_summary(),
        validation=ValidationResult(approved=False, issues=["too verbatim"]),
    )
    assert route_after_validator(state) == "compress"


def test_route_after_validator_done():
    state = GraphState(
        standup_date="2026-07-10",
        raw_updates=[],
        validation=ValidationResult(approved=True, issues=[]),
    )
    assert route_after_validator(state) == "done"
