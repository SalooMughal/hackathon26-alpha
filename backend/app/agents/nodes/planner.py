from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_structured_llm
from app.agents.preclean import extract_usage, merge_usage, run_node
from app.agents.prompts.loader import format_team_updates, load_prompt
from app.agents.state import GraphState
from app.agents.state_utils import as_graph_state
from app.schemas.plan import SummaryPlan


async def planner_node(state: GraphState | dict) -> dict:
    state = as_graph_state(state)
    if state.status == "degraded":
        return {}

    async def _run() -> dict:
        if not state.sanitized_updates:
            return {"status": "degraded", "error": "planner: missing sanitized_updates"}
        parts = load_prompt("planner_v1")
        human = parts.human_template.format(
            standup_date=state.standup_date,
            team_updates=format_team_updates(state.sanitized_updates.members),
        )
        messages = [
            SystemMessage(content=parts.system),
            HumanMessage(content=human),
        ]
        try:
            llm = get_structured_llm("planner", SummaryPlan)
            response = await llm.ainvoke(messages)
            plan: SummaryPlan = response["parsed"]
            usage = merge_usage(
                state.usage, "planner", extract_usage(response["raw"])
            )
            return {"plan": plan, "usage": usage}
        except Exception as exc:
            return {"status": "degraded", "error": f"planner: {exc}"}

    return await run_node("planner", state, _run)
