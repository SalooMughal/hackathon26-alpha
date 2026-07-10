import json

import structlog

from app.agents.state import GraphState

logger = structlog.get_logger(__name__)

_STUB_SUMMARY_JSON = json.dumps(
    {
        "tldr": "Team is progressing on backend scaffold and integration.",
        "done": [{"person": "Shahryar", "items": ["Set up repo structure"]}],
        "doing": [{"person": "Sabir", "items": ["FastAPI endpoints"]}],
        "blockers": [{"person": "Sabir", "item": "Awaiting API key", "severity": "low"}],
        "cross_links": [],
    }
)


async def summarizer_node(state: GraphState) -> dict:
    """Summarizer agent stub — returns hardcoded JSON string. Real LLM in Phase 2."""
    logger.info(
        "agent_node",
        node="summarizer",
        revision_count=state.get("revision_count", 0),
    )
    return {"raw_summary_output": _STUB_SUMMARY_JSON}
