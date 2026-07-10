import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_FIELD_LEN = 2000


def preclean_text(text: str | None) -> str:
    """Strip control chars, collapse whitespace, cap length."""
    if text is None:
        return ""
    cleaned = CONTROL_CHARS.sub("", str(text))
    cleaned = " ".join(cleaned.split())
    return cleaned[:MAX_FIELD_LEN]


def preclean_update(update: dict) -> dict:
    """Deterministic pre-clean for one member's raw update."""
    return {
        "name": preclean_text(update.get("name", "")),
        "yesterday": preclean_text(update.get("yesterday")),
        "today": preclean_text(update.get("today")),
        "blockers": preclean_text(update.get("blockers") or ""),
    }


def preclean_updates(updates: list[dict]) -> list[dict]:
    return [preclean_update(u) for u in updates]


def extract_usage(raw_message: Any) -> dict[str, int]:
    meta = getattr(raw_message, "usage_metadata", None) or {}
    return {
        "input_tokens": int(meta.get("input_tokens", 0) or 0),
        "output_tokens": int(meta.get("output_tokens", 0) or 0),
    }


def merge_usage(state_usage: dict, node: str, usage: dict[str, int]) -> dict:
    merged = dict(state_usage)
    merged[node] = usage
    return merged


async def run_node(
    node_name: str,
    state: Any,
    fn: Callable[[], Awaitable[dict]],
) -> dict:
    """Log duration and revision_count for every node invocation."""
    start = time.perf_counter()
    result = await fn()
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    revision_count = getattr(state, "revision_count", 0)
    logger.info(
        "agent_node",
        node=node_name,
        duration_ms=duration_ms,
        revision_count=revision_count,
    )
    return result
