from app.agents.validate_deterministic import (
    build_done_doing_from_source,
    deterministic_validate,
    is_real_blocker,
    merge_summary_with_source_fields,
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


def test_merge_summary_replaces_llm_done_doing_when_swapped():
    members = [
        SanitizedMember(
            name="Asad",
            yesterday="working on ui",
            today="ui completed",
            blockers="None",
            was_modified=False,
        ),
        SanitizedMember(
            name="Shahryar",
            yesterday="working on integration",
            today="integration completed",
            blockers="None",
            was_modified=False,
        ),
    ]
    llm_summary = StandupSummary(
        tldr="Wrong mapping from LLM.",
        done=[
            PersonItems(person="Asad", items=["UI work completed."]),
            PersonItems(person="Shahryar", items=["Integration work completed."]),
        ],
        doing=[
            PersonItems(person="Asad", items=["No update provided."]),
            PersonItems(person="Shahryar", items=["No update provided."]),
        ],
        blockers=[],
    )
    merged = merge_summary_with_source_fields(llm_summary, members)

    assert merged.tldr == "Wrong mapping from LLM."
    assert merged.done[0].items == ["working on ui"]
    assert merged.doing[0].items == ["ui completed"]


def test_merge_summary_uses_llm_when_grounded_in_correct_field():
    members = [
        SanitizedMember(
            name="Sabir",
            yesterday="Added summary PUT and regenerate endpoints.",
            today="Testing manual edit and regenerate flows in Postman.",
            blockers="test",
            was_modified=False,
        )
    ]
    llm_summary = StandupSummary(
        tldr="Sabir progressing on API work.",
        done=[
            PersonItems(
                person="Sabir",
                items=["Added summary PUT and regenerate endpoints to the API."],
            )
        ],
        doing=[
            PersonItems(
                person="Sabir",
                items=["Testing manual edit and regenerate flows in Postman."],
            )
        ],
        blockers=[Blocker(person="Sabir", item="Testing blocked", severity="medium")],
    )
    merged = merge_summary_with_source_fields(llm_summary, members)

    assert "regenerate endpoints" in merged.done[0].items[0]
    assert "Postman" in merged.doing[0].items[0]
    assert merged.done[0].items[0] != merged.doing[0].items[0]


def test_deterministic_validate_rejects_no_update_when_today_filled():
    summary = StandupSummary(
        tldr="Test",
        done=[PersonItems(person="Asad", items=["working on ui"])],
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


def test_deterministic_validate_passes_after_source_merge():
    members = [
        SanitizedMember(
            name="Asad",
            yesterday="working on ui",
            today="ui completed",
            blockers="None",
            was_modified=False,
        )
    ]
    llm_summary = StandupSummary(
        tldr="Sabir has a blocker.",
        done=[PersonItems(person="Asad", items=["UI work completed."])],
        doing=[PersonItems(person="Asad", items=["No update provided."])],
        blockers=[],
    )
    merged = merge_summary_with_source_fields(llm_summary, members)
    ok, issues = deterministic_validate(
        merged,
        ["Asad"],
        source_yesterday={"Asad": "working on ui"},
        source_today={"Asad": "ui completed"},
    )
    assert ok
    assert issues == []
