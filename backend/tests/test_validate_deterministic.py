from app.agents.validate_deterministic import (
    build_done_doing_from_source,
    deterministic_validate,
    is_real_blocker,
    normalize_blocker_text,
    normalize_standup_summary,
)
from app.schemas.sanitized import SanitizedMember
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


def test_build_done_doing_from_source_maps_fields_strictly():
    members = [
        SanitizedMember(
            name="Asad",
            yesterday="working on ui",
            today="ui completed",
            blockers="None",
            was_modified=False,
        ),
        SanitizedMember(
            name="Sabir",
            yesterday="Added summary PUT and regenerate endpoints.",
            today="1111Testing manual edit and regenerate flows in Postman.",
            blockers="test",
            was_modified=False,
        ),
    ]
    done, doing = build_done_doing_from_source(members)

    assert done[0].person == "Asad"
    assert done[0].items == ["working on ui"]
    assert doing[0].items == ["ui completed"]
    assert done[1].items == ["Added summary PUT and regenerate endpoints."]
    assert doing[1].items == ["1111Testing manual edit and regenerate flows in Postman."]


def test_build_done_doing_empty_today_is_no_update():
    members = [
        SanitizedMember(
            name="Zaha",
            yesterday="working on api",
            today="",
            blockers="None",
            was_modified=False,
        )
    ]
    _, doing = build_done_doing_from_source(members)
    assert doing[0].items == ["No update provided"]


def test_deterministic_validate_rejects_first_person():
    summary = StandupSummary(
        tldr="Hackathon progress.",
        done=[
            PersonItems(
                person="Asad",
                items=["I was working on UI components for hackathon proj"],
            )
        ],
        doing=[PersonItems(person="Asad", items=["Completed UI components"])],
        blockers=[],
    )
    ok, issues = deterministic_validate(summary, ["Asad"])
    assert not ok
    assert any("third person" in issue for issue in issues)


def test_deterministic_validate_rejects_field_swap():
    summary = StandupSummary(
        tldr="Wrong mapping from LLM.",
        done=[PersonItems(person="Asad", items=["UI work completed."])],
        doing=[PersonItems(person="Asad", items=["No update provided"])],
        blockers=[],
    )
    ok, issues = deterministic_validate(
        summary,
        ["Asad"],
        source_yesterday={"Asad": "working on ui"},
        source_today={"Asad": "ui completed"},
    )
    assert not ok
    assert any("today field" in issue or "yesterday field" in issue for issue in issues)


def test_deterministic_validate_rejects_no_update_when_today_filled():
    summary = StandupSummary(
        tldr="Test",
        done=[PersonItems(person="Asad", items=["Continued UI work"])],
        doing=[PersonItems(person="Asad", items=["No update provided"])],
        blockers=[],
    )
    ok, issues = deterministic_validate(
        summary,
        ["Asad"],
        source_today={"Asad": "ui completed"},
    )
    assert not ok
    assert any("today field" in issue for issue in issues)


def test_deterministic_validate_rejects_verbatim_copy():
    summary = StandupSummary(
        tldr="Hackathon progress.",
        done=[
            PersonItems(
                person="Asad",
                items=["working on ui components for hackathon proj"],
            )
        ],
        doing=[
            PersonItems(
                person="Asad",
                items=["ui componenets for hackathon completed"],
            )
        ],
        blockers=[],
    )
    ok, issues = deterministic_validate(
        summary,
        ["Asad"],
        source_yesterday={
            "Asad": "i was working ui components for hackathon proj",
        },
        source_today={"Asad": "ui componenets for hackathon completed"},
    )
    assert not ok
    assert any("verbatim" in issue for issue in issues)


def test_deterministic_validate_passes_third_person_summary():
    summary = StandupSummary(
        tldr="Hackathon UI and API work is wrapping up.",
        done=[
            PersonItems(
                person="Asad",
                items=["Built UI components for the hackathon project"],
            ),
            PersonItems(
                person="Zaha",
                items=["Developed API endpoints for the hackathon"],
            ),
        ],
        doing=[
            PersonItems(
                person="Asad",
                items=["Completed UI components for the hackathon"],
            ),
            PersonItems(
                person="Zaha",
                items=["Finished API work for the hackathon"],
            ),
        ],
        blockers=[],
    )
    ok, issues = deterministic_validate(
        summary,
        ["Asad", "Zaha"],
        source_yesterday={
            "Asad": "i was working ui components for hackathon proj",
            "Zaha": "working on api for hackathon",
        },
        source_today={
            "Asad": "ui componenets for hackathon completed",
            "Zaha": "api completed for hackathon",
        },
    )
    assert ok
    assert issues == []
