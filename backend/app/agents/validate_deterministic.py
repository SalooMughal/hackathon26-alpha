import re

from app.schemas.summary import Blocker, StandupSummary

_NONE_BLOCKER = re.compile(
    r"^(none|n/a|na|no blockers?|nothing|nil|-|—|\.)$", re.IGNORECASE
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


def deterministic_validate(
    summary: StandupSummary,
    member_names: list[str],
    source_blockers: dict[str, str] | None = None,
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
