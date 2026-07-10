import re

from app.schemas.sanitized import SanitizedMember
from app.schemas.summary import Blocker, PersonItems, StandupSummary

_NONE_BLOCKER = re.compile(
    r"^(none|n/a|na|no blockers?|nothing|nil|-|—|\.)$", re.IGNORECASE
)
_NO_UPDATE = "No update provided"


def is_real_blocker(text: str | None) -> bool:
    """True when the text represents an actual blocker, not a placeholder."""
    if text is None:
        return False
    cleaned = " ".join(str(text).strip().split())
    if not cleaned:
        return False
    return _NONE_BLOCKER.match(cleaned) is None


def normalize_blocker_text(text: str | None) -> str:
    """Convert placeholder blocker values to empty string."""
    if not is_real_blocker(text):
        return ""
    return " ".join(str(text).strip().split())


def _field_has_content(text: str | None) -> bool:
    if text is None:
        return False
    return bool(str(text).strip())


def _section_item(text: str | None) -> str:
    """Map a source field to a single summary item."""
    if not _field_has_content(text):
        return _NO_UPDATE
    return " ".join(str(text).strip().split())


def build_done_doing_from_source(
    members: list[SanitizedMember],
) -> tuple[list[PersonItems], list[PersonItems]]:
    """Build Done/Doing strictly from each member's yesterday and today fields."""
    done: list[PersonItems] = []
    doing: list[PersonItems] = []
    for member in members:
        done.append(
            PersonItems(person=member.name, items=[_section_item(member.yesterday)])
        )
        doing.append(
            PersonItems(person=member.name, items=[_section_item(member.today)])
        )
    return done, doing


def _normalize_compare(text: str) -> str:
    return " ".join(str(text).lower().strip().split())


def _item_grounded_in_source(item: str, source: str) -> bool:
    """True when a summary item plausibly condenses the source field."""
    item_n = _normalize_compare(item)
    source_n = _normalize_compare(source)
    if not source_n or item_n == _NO_UPDATE.lower():
        return False
    if source_n in item_n or item_n in source_n:
        return True
    source_words = {w for w in source_n.split() if len(w) > 2}
    if not source_words:
        source_words = set(source_n.split())
    item_words = set(item_n.split())
    overlap = source_words & item_words
    threshold = min(2, len(source_words))
    return len(overlap) >= threshold


def _pick_section_items(
    llm_items: list[str] | None,
    source_text: str,
    other_field_text: str,
) -> list[str]:
    """Prefer LLM-polished items when grounded in the correct source field."""
    fallback = [_section_item(source_text)]
    if not llm_items:
        return fallback
    candidate = " ".join(str(i).strip() for i in llm_items if str(i).strip())
    if not candidate or candidate.lower() == _NO_UPDATE.lower():
        return fallback
    grounded_in_source = _item_grounded_in_source(candidate, source_text)
    grounded_in_other = _item_grounded_in_source(candidate, other_field_text)
    if grounded_in_source and not grounded_in_other:
        return [candidate]
    if grounded_in_source and grounded_in_other:
        return fallback
    return fallback


def merge_summary_with_source_fields(
    summary: StandupSummary,
    members: list[SanitizedMember],
) -> StandupSummary:
    """Keep LLM tldr/blockers/cross_links; merge done/doing with source-aware polish."""
    llm_done = {p.person: p.items for p in summary.done}
    llm_doing = {p.person: p.items for p in summary.doing}

    done: list[PersonItems] = []
    doing: list[PersonItems] = []
    for member in members:
        done.append(
            PersonItems(
                person=member.name,
                items=_pick_section_items(
                    llm_done.get(member.name),
                    member.yesterday,
                    member.today,
                ),
            )
        )
        doing.append(
            PersonItems(
                person=member.name,
                items=_pick_section_items(
                    llm_doing.get(member.name),
                    member.today,
                    member.yesterday,
                ),
            )
        )
    return summary.model_copy(update={"done": done, "doing": doing})


def normalize_standup_summary(
    summary: StandupSummary,
    source_blockers: dict[str, str] | None = None,
) -> StandupSummary:
    """Strip faux/hallucinated blockers and tighten summary before validation."""
    blockers: list[Blocker] = []
    for b in summary.blockers:
        if not is_real_blocker(b.item):
            continue
        if source_blockers is not None:
            source = source_blockers.get(b.person, "")
            if not is_real_blocker(source):
                continue
        blockers.append(
            Blocker(person=b.person, item=b.item.strip(), severity=b.severity)
        )
    return summary.model_copy(update={"blockers": blockers})


def _items_include_no_update(items: list[str]) -> bool:
    return any(item.strip().lower() == _NO_UPDATE.lower() for item in items)


def deterministic_validate(
    summary: StandupSummary,
    member_names: list[str],
    source_blockers: dict[str, str] | None = None,
    source_yesterday: dict[str, str] | None = None,
    source_today: dict[str, str] | None = None,
) -> tuple[bool, list[str]]:
    """Code-side checks before/alongside the LLM validator."""
    issues: list[str] = []

    if not summary.tldr.strip():
        issues.append("TL;DR must not be empty.")

    names_done = {p.person for p in summary.done}
    names_doing = {p.person for p in summary.doing}

    for name in member_names:
        if name not in names_done:
            issues.append(f"Add {name} to the done section.")
        if name not in names_doing:
            issues.append(f"Add {name} to the doing section.")

    if source_yesterday is not None:
        for section in summary.done:
            if (
                _items_include_no_update(section.items)
                and _field_has_content(source_yesterday.get(section.person, ""))
            ):
                issues.append(
                    f"{section.person} done section must use their yesterday field, "
                    "not 'No update provided'."
                )

    if source_today is not None:
        for section in summary.doing:
            if (
                _items_include_no_update(section.items)
                and _field_has_content(source_today.get(section.person, ""))
            ):
                issues.append(
                    f"{section.person} doing section must use their today field, "
                    "not 'No update provided'."
                )

    for blocker in summary.blockers:
        if not is_real_blocker(blocker.item):
            issues.append(
                f"Remove blocker entry for {blocker.person} — no real blocker in input."
            )
        elif source_blockers is not None and not is_real_blocker(
            source_blockers.get(blocker.person, "")
        ):
            issues.append(
                f"Remove invented blocker for {blocker.person} — input had no blocker."
            )

    return len(issues) == 0, issues[:5]
