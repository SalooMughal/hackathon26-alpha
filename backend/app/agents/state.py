from typing import TypedDict


class GraphState(TypedDict, total=False):
    """LangGraph state — wired in Phase 2."""

    team_updates: list[dict]
    plan: dict | None
    raw_summary_output: str | None
    parsed_summary: dict | None
    validation: dict | None
    feedback: str | None
    revision_count: int
    status: str
