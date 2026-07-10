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
from app.schemas.sanitized import SanitizedMember
from app.schemas.summary import StandupSummary
from app.schemas.validation import ValidationResult


def _members_from_state(state: GraphState) -> list[SanitizedMember]:
    if state.sanitized_updates and state.sanitized_updates.members:
        return state.sanitized_updates.members
    if state.raw_updates:
        from app.agents.preclean import preclean_updates

        return [
            SanitizedMember(
                name=u["name"],
                yesterday=u["yesterday"],
                today=u["today"],
                blockers=u["blockers"],
                was_modified=False,
            )
            for u in preclean_updates(state.raw_updates)
        ]
    return []


async def compressor_node(state: GraphState | dict) -> dict:
    """Produce a fully AI-synthesized concise summary (never verbatim source)."""
    state = as_graph_state(state)

    async def _run() -> dict:
        members = _members_from_state(state)
        if not members:
            return {"status": "degraded", "error": "compressor: no team updates"}

        parts = load_prompt("compressor_v1")
        plan_block = ""
        if state.plan:
            plan_block = f"\n<plan>\n{state.plan.model_dump_json(indent=2)}\n</plan>"

        human = parts.human_template.format(
            standup_date=state.standup_date,
            team_updates=format_team_updates(members),
            plan_block=plan_block,
        )
        messages = [
            SystemMessage(content=parts.system),
            HumanMessage(content=human),
        ]

        try:
            llm = get_structured_llm("summarizer", StandupSummary)
            response = await llm.ainvoke(messages)
            summary: StandupSummary = response["parsed"]
            source_blockers = {m.name: m.blockers for m in members}
            summary = normalize_standup_summary(
                summary, source_blockers=source_blockers
            )

            member_names = [m.name for m in members]
            source_yesterday = {m.name: m.yesterday for m in members}
            source_today = {m.name: m.today for m in members}
            ok, issues = deterministic_validate(
                summary,
                member_names,
                source_blockers=source_blockers,
                source_yesterday=source_yesterday,
                source_today=source_today,
            )
            usage = merge_usage(
                state.usage, "compressor", extract_usage(response["raw"])
            )

            if ok:
                return {
                    "parsed_summary": summary,
                    "validation": ValidationResult(approved=True, issues=[]),
                    "status": "validated",
                    "usage": usage,
                }

            return {
                "parsed_summary": summary,
                "validation": ValidationResult(approved=False, issues=issues),
                "status": "degraded",
                "error": "compressor: summary still failed quality checks",
                "usage": usage,
            }
        except Exception as exc:
            return {"status": "degraded", "error": f"compressor: {exc}"}

    return await run_node("compressor", state, _run)
