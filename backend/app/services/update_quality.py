"""Standup input quality gate — reject placeholders and non-actionable filler."""

import re

_MIN_WORDS = 4
_MIN_CHARS = 24

_TRIVIAL_WORDS = frozenset(
    {
        "test",
        "testing",
        "asdf",
        "dummy",
        "sample",
        "foo",
        "bar",
        "hello",
        "ok",
        "good",
        "stuff",
        "things",
        "work",
        "update",
        "todo",
        "wip",
        "na",
        "none",
        "yes",
        "no",
        "idk",
        "tbd",
    }
)

_PLACEHOLDER_ONLY = re.compile(
    r"^(?:\.+|x+|asdf|qwer|aaa+|zzz+)$",
    re.IGNORECASE,
)

_GENERIC_PHRASE = re.compile(
    r"^(?:"
    r"(?:\w+\s+){0,2}(?:completed|complete|done|finished)"
    r"|working on \w+"
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


def _is_trivial_only(words: list[str]) -> bool:
    return bool(words) and all(w.lower() in _TRIVIAL_WORDS for w in words)


def _is_insufficient_field(text: str) -> bool:
    cleaned = _normalize(text)
    if not cleaned or len(cleaned) <= 1:
        return True

    words = cleaned.split()
    wc = len(words)

    if wc == 1:
        return True
    if wc == 2 and len(cleaned) < _MIN_CHARS:
        return True
    if len(set(w.lower() for w in words)) == 1:
        return True
    if _is_trivial_only(words):
        return True
    if wc < _MIN_WORDS and len(cleaned) < _MIN_CHARS:
        return True
    if _LEADING_GARBAGE.match(cleaned):
        return True
    if _GENERIC_PHRASE.match(cleaned):
        return True
    if wc <= 3 and re.search(
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
    Reject updates that are placeholders, repeated junk, or too thin to be
    a real standup (e.g. 'test', 'ui completed'). Needs a few words of real work context.
    """
    issues: list[str] = []

    for field_name, value in (("yesterday", yesterday), ("today", today)):
        cleaned = _normalize(value)
        if _PLACEHOLDER_ONLY.match(cleaned):
            issues.append(
                f"{field_name}: Please replace placeholder text with your actual standup update."
            )
        elif _is_insufficient_field(cleaned):
            issues.append(
                f"{field_name}: Please describe your work with a bit more detail — "
                f"what you finished or plan to do (at least a short sentence, not "
                f"single words like 'test' or generic lines like 'ui completed')."
            )

    return issues
