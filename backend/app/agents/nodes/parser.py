import json
import re

from app.agents.preclean import run_node
from app.agents.state import GraphState
from app.agents.state_utils import as_graph_state
from app.schemas.summary import StandupSummary

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _extract_json(raw: str) -> str:
    text = raw.strip()
    text = _FENCE_RE.sub("", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start : end + 1]


async def parser_node(state: GraphState | dict) -> dict:
    state = as_graph_state(state)
    if state.status == "degraded":
        return {}

    async def _run() -> dict:
        raw = state.raw_summary_output
        if not raw:
            return {
                "parsed_summary": None,
                "feedback": (
                    "Your previous output was invalid JSON or failed schema validation: "
                    "empty output. Return only a single valid JSON object matching the schema."
                ),
                "revision_count": state.revision_count + 1,
            }
        try:
            payload = json.loads(_extract_json(raw))
            summary = StandupSummary.model_validate(payload)
            from app.agents.validate_deterministic import (
                merge_summary_with_source_fields,
                normalize_standup_summary,
            )

            source_blockers = None
            if state.sanitized_updates:
                summary = merge_summary_with_source_fields(
                    summary, state.sanitized_updates.members
                )
                source_blockers = {
                    m.name: m.blockers for m in state.sanitized_updates.members
                }
            summary = normalize_standup_summary(
                summary, source_blockers=source_blockers
            )
            return {"parsed_summary": summary}
        except (json.JSONDecodeError, ValueError) as exc:
            short_error = str(exc)[:200]
            return {
                "parsed_summary": None,
                "feedback": (
                    "Your previous output was invalid JSON or failed schema validation: "
                    f"{short_error}. Return only a single valid JSON object matching the schema."
                ),
                "revision_count": state.revision_count + 1,
            }

    return await run_node("parser", state, _run)
