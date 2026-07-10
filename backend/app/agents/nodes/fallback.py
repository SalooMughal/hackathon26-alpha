from app.agents.preclean import run_node
from app.agents.state import GraphState
from app.agents.state_utils import as_graph_state
from app.schemas.summary import Blocker, PersonItems, StandupSummary


async def fallback_node(state: GraphState | dict) -> dict:
    state = as_graph_state(state)
    async def _run() -> dict:
        members = (
            state.sanitized_updates.members
            if state.sanitized_updates
            else []
        )
        if not members and state.raw_updates:
            from app.schemas.sanitized import SanitizedMember

            from app.agents.preclean import preclean_updates

            members = [
                SanitizedMember(
                    name=u["name"],
                    yesterday=u["yesterday"],
                    today=u["today"],
                    blockers=u["blockers"],
                    was_modified=False,
                )
                for u in preclean_updates(state.raw_updates)
            ]

        done: list[PersonItems] = []
        doing: list[PersonItems] = []
        blockers: list[Blocker] = []
        for member in members:
            if member.yesterday:
                done.append(PersonItems(person=member.name, items=[member.yesterday]))
            if member.today:
                doing.append(PersonItems(person=member.name, items=[member.today]))
            if member.blockers:
                blockers.append(
                    Blocker(
                        person=member.name,
                        item=member.blockers,
                        severity="medium",
                    )
                )

        summary = StandupSummary(
            tldr="Auto-generated summary — AI validation unavailable.",
            done=done,
            doing=doing,
            blockers=blockers,
            cross_links=[],
        )
        return {"parsed_summary": summary, "status": "degraded"}

    return await run_node("fallback", state, _run)
