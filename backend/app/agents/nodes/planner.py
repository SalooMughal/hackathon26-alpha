import structlog

from app.agents.state import GraphState

logger = structlog.get_logger(__name__)


async def planner_node(state: GraphState) -> dict:
    """Planner agent stub — returns a fixed plan. Real LLM logic in Phase 2."""
    logger.info("agent_node", node="planner", revision_count=state.get("revision_count", 0))
    return {
        "plan": {
            "sections_order": ["done", "doing", "blockers"],
            "grouping_strategy": "by_section",
            "tone": "concise",
            "emphasis": [],
        }
    }
