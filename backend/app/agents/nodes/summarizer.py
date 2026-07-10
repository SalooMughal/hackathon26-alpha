from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.preclean import extract_usage, merge_usage, run_node
from app.agents.prompts.loader import format_team_updates, load_prompt
from app.agents.state import GraphState
from app.agents.state_utils import as_graph_state


async def summarizer_node(state: GraphState | dict) -> dict:
    state = as_graph_state(state)
    if state.status == "degraded":
        return {}

    async def _run() -> dict:
        if not state.sanitized_updates or not state.plan:
            return {
                "status": "degraded",
                "error": "summarizer: missing sanitized_updates or plan",
            }
        parts = load_prompt("summarizer_v1")
        feedback_block = ""
        if state.feedback and parts.feedback_template:
            feedback_block = parts.feedback_template.format(feedback=state.feedback)
        human = parts.human_template.format(
            standup_date=state.standup_date,
            plan=state.plan.model_dump_json(indent=2),
            team_updates=format_team_updates(state.sanitized_updates.members),
            feedback_block=feedback_block,
        )
        messages = [
            SystemMessage(content=parts.system),
            HumanMessage(content=human),
        ]
        try:
            llm = get_llm("summarizer")
            response = await llm.ainvoke(messages)
            content = response.content
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            usage = merge_usage(
                state.usage, "summarizer", extract_usage(response)
            )
            return {
                "raw_summary_output": str(content),
                "parsed_summary": None,
                "validation": None,
                "feedback": None,
                "usage": usage,
            }
        except Exception as exc:
            return {"status": "degraded", "error": f"summarizer: {exc}"}

    return await run_node("summarizer", state, _run)
