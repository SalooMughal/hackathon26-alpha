import json

import pytest

from app.agents.nodes.parser import parser_node
from app.agents.state import GraphState

VALID_JSON = json.dumps(
    {
        "tldr": "Team is on track.",
        "done": [{"person": "Sabir", "items": ["Built API"]}],
        "doing": [{"person": "Asad", "items": ["UI work"]}],
        "blockers": [{"person": "Sabir", "item": "Need key", "severity": "low"}],
        "cross_links": [],
    }
)


def _state(raw: str, revision_count: int = 0) -> GraphState:
    return GraphState(
        standup_date="2026-07-10",
        raw_updates=[],
        raw_summary_output=raw,
        revision_count=revision_count,
    )


@pytest.mark.asyncio
async def test_parser_valid_json():
    result = await parser_node(_state(VALID_JSON))
    assert result["parsed_summary"] is not None
    assert result["parsed_summary"].tldr == "Team is on track."


@pytest.mark.asyncio
async def test_parser_fenced_json():
    result = await parser_node(_state(f"```json\n{VALID_JSON}\n```"))
    assert result["parsed_summary"] is not None


@pytest.mark.asyncio
async def test_parser_junk_wrapped_json():
    result = await parser_node(_state(f"Preamble\n{VALID_JSON}\nTrailing"))
    assert result["parsed_summary"] is not None


@pytest.mark.asyncio
async def test_parser_invalid_json_increments_revision():
    result = await parser_node(_state("not json", revision_count=0))
    assert "feedback" in result
    assert result["revision_count"] == 1
    assert result["parsed_summary"] is None


@pytest.mark.asyncio
async def test_parser_bad_severity_fails_validation():
    bad = json.dumps(
        {
            "tldr": "x",
            "done": [],
            "doing": [],
            "blockers": [{"person": "A", "item": "b", "severity": "critical"}],
            "cross_links": [],
        }
    )
    result = await parser_node(_state(bad))
    assert result.get("parsed_summary") is None
    assert result["revision_count"] == 1
