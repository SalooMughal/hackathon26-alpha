import structlog

from app.agents.state import GraphState

logger = structlog.get_logger(__name__)


async def validator_node(state: GraphState) -> dict:
    """Validator agent stub — returns approved=True. Real LLM logic in Phase 2."""
    logger.info(
        "agent_node",
        node="validator",
        revision_count=state.get("revision_count", 0),
    )
    return {"validation": {"approved": True, "issues": []}, "status": "validated"}
