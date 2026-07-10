import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_structured_llm
from app.agents.preclean import extract_usage, merge_usage, preclean_updates, run_node
from app.agents.prompts.loader import format_team_updates, load_prompt
from app.agents.state import GraphState
from app.agents.state_utils import as_graph_state
from app.schemas.sanitized import SanitizedMember, SanitizedUpdates

logger = structlog.get_logger(__name__)


def _fail_open_from_raw(raw_updates: list[dict]) -> SanitizedUpdates:
    cleaned = preclean_updates(raw_updates)
    return SanitizedUpdates(
        members=[
            SanitizedMember(
                name=u["name"],
                yesterday=u["yesterday"],
                today=u["today"],
                blockers=u["blockers"],
                was_modified=False,
                flags=[],
                fully_redacted=False,
            )
            for u in cleaned
        ],
        notes=[],
    )


def _restore_missing_members(
    result: SanitizedUpdates, raw_updates: list[dict]
) -> SanitizedUpdates:
    """Ensure every input member appears exactly once in the output."""
    cleaned_by_name = {u["name"]: u for u in preclean_updates(raw_updates)}
    output_by_name = {m.name: m for m in result.members}
    members: list[SanitizedMember] = []
    for name, raw in cleaned_by_name.items():
        if name in output_by_name:
            members.append(output_by_name[name])
        else:
            members.append(
                SanitizedMember(
                    name=name,
                    yesterday=raw["yesterday"],
                    today=raw["today"],
                    blockers=raw["blockers"],
                    was_modified=False,
                    flags=[],
                    fully_redacted=False,
                )
            )
    return SanitizedUpdates(members=members, notes=result.notes)


async def sanitizer_node(state: GraphState | dict) -> dict:
    state = as_graph_state(state)
    async def _run() -> dict:
        cleaned_raw = preclean_updates(state.raw_updates)
        parts = load_prompt("sanitizer_v1")
        human = parts.human_template.format(
            standup_date=state.standup_date,
            team_updates=format_team_updates(cleaned_raw),
        )
        messages = [
            SystemMessage(content=parts.system),
            HumanMessage(content=human),
        ]
        try:
            llm = get_structured_llm("sanitizer", SanitizedUpdates)
            response = await llm.ainvoke(messages)
            parsed: SanitizedUpdates = response["parsed"]
            sanitized = _restore_missing_members(parsed, state.raw_updates)
            usage = merge_usage(
                state.usage,
                "sanitizer",
                extract_usage(response["raw"]),
            )
            return {"sanitized_updates": sanitized, "usage": usage}
        except Exception as exc:
            logger.warning("sanitizer_fail_open", error=str(exc))
            fallback = _fail_open_from_raw(state.raw_updates)
            return {"sanitized_updates": fallback, "usage": state.usage}

    return await run_node("sanitizer", state, _run)
