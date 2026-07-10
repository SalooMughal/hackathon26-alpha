import re

from app.schemas.sanitized import SanitizedMember
from app.schemas.summary import Blocker, PersonItems, StandupSummary

_NONE_BLOCKER = re.compile(
    r"^(none|n/a|na|no blockers?|nothing|nil|-|—|\.)$", re.IGNORECASE
)
_NO_UPDATE = "No update provided"
_FIRST_PERSON = re.compile(
    r"\b(I|I'm|I've|I'd|my|me|we|we're|we've|we'd|our|us)\b", re.IGNORECASE
)


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


def _overlap_score(item: str, source: str) -> float:
    """How strongly an item reflects a source field (0.0–1.0)."""
    item_n = _normalize_compare(item)
    source_n = _normalize_compare(source)
    if not source_n or not item_n or item_n == _NO_UPDATE.lower():
        return 0.0
    if source_n in item_n or item_n in source_n:
        return 1.0
    source_words = {w for w in source_n.split() if len(w) > 2} or set(source_n.split())
    if not source_words:
        return 0.0
    item_words = set(item_n.split())
    return len(source_words & item_words) / len(source_words)


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


def _normalize_words(text: str) -> set[str]:
    cleaned = re.sub(r"[^\w\s]", " ", _normalize_compare(text))
    return {w for w in cleaned.split() if w}


def _is_near_verbatim(item: str, source: str) -> bool:
    """True when an item is essentially a copy-paste of the source field."""
    if not _field_has_content(source):
        return False
    item_words = _normalize_words(item)
    source_words = _normalize_words(source)
    if not item_words or not source_words:
        return False
    if item_words == source_words:
        return True
    overlap = item_words & source_words
    return len(overlap) / len(source_words) >= 0.85 and len(item_words) <= len(source_words) + 2


def _combined_item_text(items: list[str]) -> str:
    return " ".join(str(i).strip() for i in items if str(i).strip())


def _uses_first_person(text: str) -> bool:
    return _FIRST_PERSON.search(text) is not None


def _field_swap_issue(
    person: str,
    items: list[str],
    expected_source: str,
    other_source: str,
    section_label: str,
    expected_label: str,
    other_label: str,
) -> str | None:
    """Detect when a section item aligns more with the wrong source field."""
    if not _field_has_content(expected_source):
        return None
    text = _combined_item_text(items)
    if not text or text.lower() == _NO_UPDATE.lower():
        return None
    expected_score = _overlap_score(text, expected_source)
    other_score = _overlap_score(text, other_source)
    if other_score > expected_score + 0.15 and other_score >= 0.35:
        return (
            f"{person} {section_label} item appears to come from their {other_label} "
            f"field — rewrite using their {expected_label} field in third person."
        )
    return None


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

    if source_yesterday is not None and source_today is not None:
        for section in summary.done:
            issue = _field_swap_issue(
                section.person,
                section.items,
                source_yesterday.get(section.person, ""),
                source_today.get(section.person, ""),
                "done",
                "yesterday",
                "today",
            )
            if issue:
                issues.append(issue)
            text = _combined_item_text(section.items)
            source = source_yesterday.get(section.person, "")
            if _is_near_verbatim(text, source):
                issues.append(
                    f"{section.person}: done item copies yesterday verbatim — "
                    "rewrite in third person as a concise status line."
                )
        for section in summary.doing:
            issue = _field_swap_issue(
                section.person,
                section.items,
                source_today.get(section.person, ""),
                source_yesterday.get(section.person, ""),
                "doing",
                "today",
                "yesterday",
            )
            if issue:
                issues.append(issue)
            text = _combined_item_text(section.items)
            source = source_today.get(section.person, "")
            if _is_near_verbatim(text, source):
                issues.append(
                    f"{section.person}: doing item copies today verbatim — "
                    "rewrite in third person as a concise status line."
                )

    for section in summary.done + summary.doing:
        for item in section.items:
            if _uses_first_person(item):
                issues.append(
                    f"{section.person}: rewrite in third person — remove first-person "
                    f"wording (I/my/we) from done/doing items."
                )
                break

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
