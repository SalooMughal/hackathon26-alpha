import json

import structlog

from app.agents.state import GraphState
from app.schemas.summary import StandupSummary

logger = structlog.get_logger(__name__)


async def parser_node(state: GraphState) -> dict:
    """Deterministic JSON parser — json.loads + Pydantic validation."""
    logger.info("agent_node", node="parser", revision_count=state.get("revision_count", 0))
    raw = state.get("raw_summary_output")
    if not raw:
        return {"feedback": "No raw summary output to parse.", "status": "in_progress"}
    try:
        data = json.loads(raw)
        parsed = StandupSummary.model_validate(data)
        return {"parsed_summary": parsed.model_dump(), "feedback": None}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"feedback": str(exc), "status": "in_progress"}
