from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_structured_llm
from app.agents.preclean import extract_usage, merge_usage, run_node
from app.agents.prompts.loader import format_team_updates, load_prompt
from app.agents.state import GraphState
from app.agents.state_utils import as_graph_state
from app.schemas.validation import ValidationResult


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
        parts = load_prompt("validator_v1")
        human = parts.human_template.format(
            standup_date=state.standup_date,
            team_updates=format_team_updates(state.sanitized_updates.members),
            plan=state.plan.model_dump_json(indent=2),
            summary_json=state.parsed_summary.model_dump_json(indent=2),
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
            if result.approved:
                return {
                    "validation": result,
                    "status": "validated",
                    "usage": usage,
                }
            return {
                "validation": result,
                "feedback": "\n".join(f"- {issue}" for issue in result.issues),
                "revision_count": state.revision_count + 1,
                "usage": usage,
            }
        except Exception as exc:
            return {"status": "degraded", "error": f"validator: {exc}"}

    return await run_node("validator", state, _run)
