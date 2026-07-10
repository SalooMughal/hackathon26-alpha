import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_structured_llm
from app.agents.preclean import extract_usage, merge_usage, run_node
from app.agents.prompts.loader import format_team_updates, load_prompt
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

        members = state.sanitized_updates.members
        source_blockers = {m.name: m.blockers for m in members}
        source_yesterday = {m.name: m.yesterday for m in members}
        source_today = {m.name: m.today for m in members}
        summary = normalize_standup_summary(
            state.parsed_summary, source_blockers=source_blockers
        )
        member_names = [m.name for m in members]

        ok, det_issues = deterministic_validate(
            summary,
            member_names,
            source_blockers=source_blockers,
            source_yesterday=source_yesterday,
            source_today=source_today,
        )
        if not ok:
            logger.warning("validator_deterministic_reject", issues=det_issues)
            return {
                "parsed_summary": summary,
                "validation": ValidationResult(approved=False, issues=det_issues),
                "feedback": "\n".join(f"- {issue}" for issue in det_issues),
                "revision_count": state.revision_count + 1,
            }

        parts = load_prompt("validator_v1")
        human = parts.human_template.format(
            standup_date=state.standup_date,
            team_updates=format_team_updates(members),
            plan=state.plan.model_dump_json(indent=2),
            summary_json=summary.model_dump_json(indent=2),
        )
        messages = [
            SystemMessage(content=parts.system),
            HumanMessage(content=human),
        ]
        try:
            llm = get_structured_llm("validator", ValidationResult)
            response = await llm.ainvoke(messages)
            result: ValidationResult = response["parsed"]
            usage = merge_usage(
                state.usage, "validator", extract_usage(response["raw"])
            )
            if not result.approved:
                logger.warning("validator_llm_reject", issues=result.issues)
                return {
                    "parsed_summary": summary,
                    "validation": result,
                    "feedback": "\n".join(f"- {issue}" for issue in result.issues),
                    "revision_count": state.revision_count + 1,
                    "usage": usage,
                }
            logger.info("validator_approved")
            return {
                "parsed_summary": summary,
                "validation": result,
                "status": "validated",
                "usage": usage,
            }
        except Exception as exc:
            logger.warning("validator_llm_fail_open", error=str(exc))
            return {
                "parsed_summary": summary,
                "validation": ValidationResult(approved=True, issues=[]),
                "status": "validated",
                "usage": state.usage,
            }

    return await run_node("validator", state, _run)
