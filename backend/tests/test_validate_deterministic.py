from app.agents.validate_deterministic import (
    is_real_blocker,
    normalize_blocker_text,
    normalize_standup_summary,
)
from app.schemas.summary import Blocker, PersonItems, StandupSummary


def test_is_real_blocker():
    assert not is_real_blocker("None")
    assert not is_real_blocker("none")
    assert not is_real_blocker("N/A")
    assert is_real_blocker("Need OpenAI API key quota")


def test_normalize_blocker_text():
    assert normalize_blocker_text("None") == ""
    assert normalize_blocker_text("Waiting on API") == "Waiting on API"


def test_normalize_standup_summary_strips_none_blockers():
    summary = StandupSummary(
        tldr="Team update",
        done=[PersonItems(person="Sabir", items=["Built API"])],
        doing=[PersonItems(person="Sabir", items=["Tests"])],
        blockers=[
            Blocker(person="Asad", item="None", severity="low"),
            Blocker(person="Sabir", item="Need API key", severity="high"),
        ],
    )
    normalized = normalize_standup_summary(summary)
    assert len(normalized.blockers) == 1
    assert normalized.blockers[0].person == "Sabir"


def test_normalize_strips_hallucinated_blocker():
    summary = StandupSummary(
        tldr="Team update",
        done=[PersonItems(person="Zaha", items=["Drafted prompts"])],
        doing=[PersonItems(person="Zaha", items=["Testing"])],
        blockers=[
            Blocker(person="Sabir", item="Need API key", severity="high"),
            Blocker(person="Zaha", item="Missing API keys", severity="high"),
        ],
    )
    source = {"Sabir": "Need API key", "Zaha": ""}
    normalized = normalize_standup_summary(summary, source_blockers=source)
    assert len(normalized.blockers) == 1
    assert normalized.blockers[0].person == "Sabir"
