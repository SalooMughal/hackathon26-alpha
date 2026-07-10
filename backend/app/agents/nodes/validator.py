import structlog

from app.agents.preclean import run_node
from app.agents.state import GraphState
from app.agents.state_utils import as_graph_state
from app.agents.validate_deterministic import (
    deterministic_validate,
    normalize_standup_summary,
)
from app.schemas.validation import ValidationResult

logger = structlog.get_logger(__name__)


async def validator_node(state: GraphState | dict) -> dict:
    state = as_graph_state(state)
    if state.status == "degraded":
        return {}

    async def _run() -> dict:
        if not state.sanitized_updates or not state.plan or not state.parsed_summary:
            return {
                "status": "degraded",
                "error": "validator: missing sanitized_updates, plan, or parsed_summary",
            }

        source_blockers = {
            m.name: m.blockers for m in state.sanitized_updates.members
        }
        summary = normalize_standup_summary(
            state.parsed_summary, source_blockers=source_blockers
        )
        member_names = [m.name for m in state.sanitized_updates.members]

        ok, det_issues = deterministic_validate(
            summary, member_names, source_blockers=source_blockers
        )
        if not ok:
            logger.warning("validator_deterministic_reject", issues=det_issues)
            return {
                "parsed_summary": summary,
                "validation": ValidationResult(approved=False, issues=det_issues),
                "feedback": "\n".join(f"- {issue}" for issue in det_issues),
                "revision_count": state.revision_count + 1,
            }

        # Deterministic checks passed — approve without LLM re-review (avoids
        # nitpicks on paraphrasing and hallucinated blocker feedback loops).
        logger.info("validator_approved_deterministic")
        return {
            "parsed_summary": summary,
            "validation": ValidationResult(approved=True, issues=[]),
            "status": "validated",
            "usage": state.usage,
        }

    return await run_node("validator", state, _run)
