"""Moderate quality checks — reject generic filler, allow real standup detail."""

import re

_PLACEHOLDER_ONLY = re.compile(
    r"^(?:\.+|x+|asdf|qwer|aaa+|zzz+)$",
    re.IGNORECASE,
)

# Generic two/three-word standup filler with no real substance.
_GENERIC_PHRASE = re.compile(
    r"^(?:"
    r"(?:\w+\s+){0,2}(?:completed|complete|done|finished)"  # ui completed, api work done
    r"|working on \w+"  # working on ui
    r"|done with \w+"
    r"|finished \w+"
    r"|fix(ed)? (?:stuff|things|bugs?)"
    r"|did (?:stuff|things|work)"
    r")\.*$",
    re.IGNORECASE,
)

_LEADING_GARBAGE = re.compile(r"^\d{3,}")


def _normalize(text: str) -> str:
    return " ".join(str(text).strip().split())


def _word_count(text: str) -> int:
    return len(_normalize(text).split()) if _normalize(text) else 0


def _is_generic_filler(text: str) -> bool:
    cleaned = _normalize(text)
    if not cleaned:
        return False
    if _LEADING_GARBAGE.match(cleaned):
        return True
    if _GENERIC_PHRASE.match(cleaned):
        return True
    # Very short + only generic verbs/nouns (e.g. "ui complete", "api done")
    if _word_count(cleaned) <= 3 and re.search(
        r"\b(completed?|done|finished|working|fixing)\b", cleaned, re.IGNORECASE
    ):
        return True
    return False


def validate_update_fields(
    yesterday: str,
    today: str,
    blockers: str | None = None,
) -> list[str]:
    """
    Reject empty, placeholder, or generic filler updates (e.g. 'ui completed').
    Detailed or longer updates pass even if informal.
    """
    issues: list[str] = []

    for field_name, value in (("yesterday", yesterday), ("today", today)):
        cleaned = _normalize(value)
        if len(cleaned) <= 1:
            issues.append(
                f"{field_name}: Please enter a short description of your work."
            )
        elif _PLACEHOLDER_ONLY.match(cleaned):
            issues.append(
                f"{field_name}: Please replace placeholder text with your actual standup update."
            )
        elif _is_generic_filler(cleaned):
            issues.append(
                f"{field_name}: This update is too generic. Add what you actually "
                f"did or plan to do (e.g. 'Built the standup form in Next.js' "
                f"instead of 'ui completed')."
            )

    return issues
